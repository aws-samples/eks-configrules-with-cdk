#!/usr/bin/env python3

config_rules_by_path = {
    "Rules": {
        "dlq_rule": {
            "stack": "config_stack",
            "path": "/configrules/sechub-dl-queue/Resource",
            "rule": [
                {
                    "id": "AwsSolutions-SQS3",
                    "reason": "Queue does not require DLQ as it is already a DLQ",
                }
            ],
        },
        "framework-isComplete": {
            "stack": "eks_stack",
            "path": "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-isComplete/ServiceRole/Resource",
            "rule": [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Queue does not require DLQ as it is already a DLQ",
                }
            ],
        },
    },
}

from cdk_nag import AwsSolutionsChecks, NagSuppressions


NagSuppressions.add_resource_suppressions_by_path(
    config_stack,
    "/configrules/sechub-dl-queue/Resource",
    [
        {
            "id": "AwsSolutions-SQS3",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-isComplete/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "/eksconfigexample/poc/Resource/CreationRole/DefaultPolicy/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/OnEventHandler/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "/eksconfigexample/@aws-cdk--aws-eks.KubectlProvider/Provider/framework-onEvent/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "/eksconfigexample/@aws-cdk--aws-eks.KubectlProvider/Handler/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-onTimeout/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/Provider/framework-onEvent/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_resource_suppressions_by_path(
    eks_stack,
    "/eksconfigexample/@aws-cdk--aws-eks.ClusterResourceProvider/IsCompleteHandler/ServiceRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
),
NagSuppressions.add_stack_suppressions(
    eks_stack,
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "We are using managed policies for this sample",
        }
    ],
)
NagSuppressions.add_stack_suppressions(
    config_stack,
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "We are using managed policies for this sample",
        }
    ],
)
Aspects.of(app).add(AwsSolutionsChecks())
app.synth()

################## CFN Nag suppressions #####################################################################
# NagSuppressions.add_resource_suppressions_by_path(
#     self,
#     '/configrules/sechub-dl-queue/',
#     [
#         {
#             "id": "AwsSolutions-SQS3",
#             "reason": "Queue does not require DLQ as it is already a DLQ",
#         }
#     ]
# )
