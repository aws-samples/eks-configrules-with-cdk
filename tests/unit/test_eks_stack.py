import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import assertions
from aws_cdk.assertions import Template
from aws_cdk.assertions import Match
from aws_cdk import aws_iam as iam

from eks_cis_cdk.config_cis_cdk_stack import lambdaStack
from eks_cis_cdk.eks_cis_cdk_stack import CdkConfigEksStack

trusted_registries = "111111111111.dkr.ecr.us-east-1.amazonaws.com,busybox"
app = cdk.App()
eks_admin_rolename = (
    "Admin"  # Set this to the Admin role in your AWS account, this is typically 'Admin'
)

eks_stack = CdkConfigEksStack(
    app, "eksconfigexample", eks_admin_rolename=eks_admin_rolename
)

config_stack = lambdaStack(
    app,
    "configrules",
    eks_lambda_role=eks_stack.lambda_role,
    eks_cluster=eks_stack.cluster.cluster_name,
    trusted_registries=trusted_registries,
)

"""Checks that the requisite IAM roles are created"""
# class TestCdkPyStack(cdk.Stack):
def test_iam_roles():
    template = assertions.Template.from_stack(eks_stack)
    template.resource_count_is("AWS::IAM::Role", 5)
    """Validate that the specified Admin rolename can assume the EKS Admin role"""
    template.has_resource_properties(
        "AWS::IAM::Role",
        Match.object_like(
            {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": {
                                    "Fn::Join": [
                                        "",
                                        ["ec2.", {"Ref": "AWS::URLSuffix"}],
                                    ]
                                }
                            },
                        },
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "arn:aws:iam::",
                                            {"Ref": "AWS::AccountId"},
                                            ":role/Admin",
                                        ],
                                    ]
                                }
                            },
                        },
                    ],
                    "Version": "2012-10-17",
                },
                "RoleName": "eks-cluster-role",
            }
        ),
    )


"""Checks that the network resources are provisioned"""


def test_network():
    template = assertions.Template.from_stack(eks_stack)
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::EC2::Subnet", 4)
    template.resource_count_is("AWS::EC2::Route", 4)


"""Tests that an EKS cluster will be created"""


def test_eks_configuration():
    template = assertions.Template.from_stack(eks_stack)
    envCapture = assertions.Capture()
    template.resource_count_is("Custom::AWSCDK-EKS-Cluster", 1)
    template.has_resource_properties(
        "Custom::AWSCDK-EKS-Cluster",
        {
            "Config": {
                "version": "1.21",
            }
        },
    )
    template.has_resource_properties(
        "AWS::EKS::Nodegroup",
        {"ScalingConfig": {"DesiredSize": 2, "MaxSize": 2, "MinSize": 2}},
    )


"""Validates that one security group has been provisioned"""


def test_security_group():
    template = assertions.Template.from_stack(eks_stack)
    envCapture = assertions.Capture()
    template.resource_count_is("AWS::EC2::SecurityGroup", 1)
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupEgress": [
                {
                    "CidrIp": "0.0.0.0/0",
                }
            ]
        },
    )
    """Validates that there are zero ingress rules in the created security group"""
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup", {"SecurityGroupIngress": Match.absent()}
    )


"""Validates the manifest resources will be created by CDK"""


def test_kubernetes_manifest_resources():
    template = assertions.Template.from_stack(eks_stack)
    envCapture = assertions.Capture()
    template.resource_count_is("Custom::AWSCDK-EKS-KubernetesResource", 4)


"""Test KMS Key should be created"""


def test_kms_keys():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::KMS::Key", 1)


"""Tests the requisite number of IAM roles are created"""


def test_iam_roles_config():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::IAM::Role", 1)
    template.has_resource_properties(
        "AWS::IAM::Role",
        (
            {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                        }
                    ]
                }
            }
        ),
    )


def test_sqs_resources():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::SQS::Queue", 2)
    template.resource_count_is("AWS::SQS::QueuePolicy", 1)
    """Checks that the SQS Queue resources have KMS key id associated"""
    template.has_resource_properties(
        "AWS::SQS::Queue",
        Match.object_like(
            {"KmsMasterKeyId": {"Fn::GetAtt": [Match.any_value(), "Arn"]}}
        ),
    )


"""Checks that the number of Lambda functions required will be created"""


def test_lambda_resources():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::Lambda::Function", 6)
    template.resource_count_is("AWS::Lambda::Permission", 5)
    template.has_resource_properties(
        "AWS::Lambda::Permission",
        {"Action": "lambda:InvokeFunction", "Principal": "config.amazonaws.com"},
    )
    """Validate that Lambda function has layer configuration"""
    template.has_resource_properties(
        "AWS::Lambda::Function", {"Layers": [{"Ref": Match.any_value()}]}
    )


def test_lambda_layer():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion", {"CompatibleRuntimes": ["python3.9"]}
    )


"""Checks that the config resources will be created"""


def test_config_resources():
    template = assertions.Template.from_stack(config_stack)
    template.resource_count_is("AWS::Config::ConfigRule", 5)
    template.has_resource_properties(
        "AWS::Config::ConfigRule",
        {
            "Source": {
                "Owner": "CUSTOM_LAMBDA",
                "SourceDetails": [
                    {
                        "EventSource": "aws.config",
                        "MaximumExecutionFrequency": "One_Hour",
                        "MessageType": "ScheduledNotification",
                    }
                ],
            }
        },
    )
