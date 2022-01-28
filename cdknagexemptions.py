#!/usr/bin/env python3

config_rules_by_path = {
    "config_rules": {
        "Rules": [
            {
                "Name": "dlq_rule",
                "stack": "config_stack",
                "path": "/configrules/sechub-dl-queue/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-SQS3",
                        "reason": "Queue does not require DLQ as it is already a DLQ",
                    }
                ],
            },
            {
                "Name": "cis-lambda-role",
                "stack": "config_stack",
                "path": "/configrules/eks-cis-lambda-role/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM5",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            }
        ],
    },
    "eks_rules": {
        "Rules": [
            {
                "Name": "dlq_rule",
                "stack": "eks_stack",
                "path": "/configrules/sechub-dl-queue/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-SQS3",
                        "reason": "Queue does not require DLQ as it is already a DLQ",
                    }
                ],
            },
            {
                "Name": "framework-isComplete",
                "stack": "eks_stack",
                "path": "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-isComplete/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "CreationRole",
                "stack": "eks_stack",
                "path": "/eksconfigexample/poc/Resource/CreationRole/DefaultPolicy/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "OnEventHandler",
                "stack": "eks_stack",
                "path": "eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/OnEventHandler/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "framework-onEvent",
                "stack": "eks_stack",
                "path": "/eksconfigexample/@aws-cdk--aws-eks.KubectlProvider/Provider/framework-onEvent/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "Handler",
                "stack": "eks_stack",
                "path": "/eksconfigexample/@aws-cdk--aws-eks.KubectlProvider/Handler/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "framework-onTimeout",
                "stack": "eks_stack",
                "path": "eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-onTimeout/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "IsCompleteHandler",
                "stack": "eks_stack",
                "path": "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/IsCompleteHandler/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "OtherFrameworkOnEvent",
                "stack": "eks_stack",
                "path": "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-onEvent/ServiceRole/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "EksAdmin",
                "stack": "eks_stack",
                "path": "/eksconfigexample/eksadmin/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            },
            {
                "Name": "EksAdmin",
                "stack": "eks_stack",
                "path": "/eksconfigexample/eksadmin/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    },
                    {
                        "id": "AwsSolutions-IAM5",
                        "reason": "Wildcard rules for this resource for demonstration purposes, resource should be locked down further for production use",
                    },
                ],
            },
            {
                "Name": "cis-lambda-role",
                "stack": "eks_stack",
                "path": "/configrules/eks-cis-lambda-role/Resource",
                "rule": [
                    {
                        "id": "AwsSolutions-IAM4",
                        "reason": "We are using AWS Managed Policy",
                    }
                ],
            }
        ],
    },
}
