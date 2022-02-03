from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_eks as eks,
    CfnOutput,
    Stack
)

from aws_cdk import Environment, Aws

env_name = "poc"

"""Creates an EKS cluster and VPC"""


class CdkConfigEksStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,eks_admin_rolename:iam.Role, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.lambda_role = iam.Role(
            scope=self,
            id="eks-cis-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="cdk-lambda-role-eks",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "ConfigPutEvaluations": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "config:PutEvaluations",
                                "config:DescribeConfigRules",
                                "config:DescribeConfigRuleEvaluationStatus",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "EKSDescribe": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "eks:ListNodegroups",
                                "eks:DescribeFargateProfile",
                                "eks:ListTagsForResource",
                                "eks:ListAddons",
                                "eks:DescribeAddon",
                                "eks:ListFargateProfiles",
                                "eks:DescribeNodegroup",
                                "eks:DescribeIdentityProviderConfig",
                                "eks:ListUpdates",
                                "eks:DescribeUpdate",
                                "eks:AccessKubernetesApi",
                                "eks:DescribeCluster",
                                "eks:ListClusters",
                                "eks:DescribeAddonVersions",
                                "eks:ListIdentityProviderConfigs",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            },
        )

        self.vpc = ec2.Vpc(
            self,
            "demovpc",
            cidr="192.168.50.0/24",
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26,
                ),
                ec2.SubnetConfiguration(
                    name="Private-Subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=26,
                ),
            ],
            nat_gateways=1,
        )
        priv_subnets = [subnet.subnet_id for subnet in self.vpc.private_subnets]

        count = 1
        for psub in priv_subnets:
            ssm.StringParameter(
                self,
                "private-subnet-" + str(count),
                string_value=psub,
                parameter_name="/" + env_name + "/private-subnet-" + str(count),
            )
            count += 1

        admin_role = "arn:aws:iam::" + Aws.ACCOUNT_ID + ":role/" + eks_admin_rolename
        eks_role = iam.Role(
            self,
            id="eksadmin",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"), iam.ArnPrincipal(admin_role)
            ),
            role_name="eks-cluster-role",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name="AdministratorAccess"
                )
            ],
        )

        eks_instance_profile = iam.CfnInstanceProfile(
            self,
            "instanceprofile",
            roles=[eks_role.role_name],
            instance_profile_name="eks-cluster-role",
        )

        self.cluster = eks.Cluster(
            self,
            env_name,
            cluster_name="secaod-" + env_name + "-eks-cluster",
            version=eks.KubernetesVersion.V1_21,
            vpc=self.vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)],
            default_capacity=0,
            masters_role=eks_role,
        )

        cluster_lambda_role = self.cluster.aws_auth.add_role_mapping(
            role=self.lambda_role, groups=["lambda-read-only"], username="lambda"
        )

        nodegroup = self.cluster.add_nodegroup_capacity(
            "eks-nodegroup",
            instance_types=[ec2.InstanceType("t2.medium")],
            disk_size=50,
            min_size=2,
            max_size=2,
            desired_size=2,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),
            capacity_type=eks.CapacityType.SPOT,
        )

        # eksclustername = core.CfnOutput(self,'eksclustername',value=cluster,description='EKS Cluster name')
        """Create Role for Lambda Function"""
        lambda_cluster_role = self.cluster.add_manifest(
            "lambdarole",
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {
                    "annotations": {
                        "rbac.authorization.kubernetes.io/autoupdate": "true"
                    },
                    "name": "lambda-read-only",
                    "namespace": "default",
                },
                "rules": [
                    {
                        "apiGroups": [""],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["extensions"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["apps"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["networking.k8s.io"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                ],
            },
        )

        lambda_cluster_role_binding = self.cluster.add_manifest(
            "ClusterRoleBinding",
            {
                "kind": "ClusterRoleBinding",
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "metadata": {
                    "name": "lambda-read-only-binding",
                    "namespace": "default",
                },
                "subjects": [
                    {
                        "kind": "User",
                        "name": "lambda",
                        "apiGroup": "rbac.authorization.k8s.io",
                    }
                ],
                "roleRef": {
                    "kind": "ClusterRole",
                    "name": "lambda-read-only",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
        )

        """creates insecure k8s deployment"""
        eks_deployment = self.cluster.add_manifest(
            "InsecureDeployment",
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": "insecure-deployment",
                    "labels": {"app": "insecure"},
                },
                "spec": {
                    "replicas": 3,
                    "selector": {"matchLabels": {"app": "insecure"}},
                    "template": {
                        "metadata": {"labels": {"app": "insecure"}},
                        "spec": {
                            "containers": [
                                {
                                    "name": "insecurecontainer",
                                    "image": "k8s.gcr.io/pause:latest",
                                    "securityContext": {
                                        "runAsUser": 2000,
                                        "allowPrivilegeEscalation": True,
                                    },
                                    "ports": [{"containerPort": 80}],
                                }
                            ]
                        },
                    },
                },
            },
        )

        """Stack Outputs"""
        eks_output = CfnOutput(
            self,
            "eks_output",
            value=self.cluster.cluster_name,
            export_name="eksclustername",
        )
        eksiam_output = CfnOutput(
            self, "iam_output", value=eks_role.role_arn, export_name="eksclusteriamrole"
        )
        lambda_role_arn = CfnOutput(
            self,
            "lambda_arn",
            value=self.lambda_role.role_arn,
            export_name="ekslambdarolearn",
        )
