#!/usr/bin/env python3

from tabnanny import verbose
from aws_cdk import App, Aspects
from eks_cis_cdk.eks_cis_cdk_stack import CdkConfigEksStack
from eks_cis_cdk.config_cis_cdk_stack import lambdaStack
from cdk_nag import AwsSolutionsChecks, NagSuppressions

# from config_cis_cdk.eks_cis_cdk_stack import lambdaStack
# from eks_cis_cdk.eks_test_stack import lambdaTestStack

############### Deployment Parameters ####################################################################
eks_admin_rolename = (
    "Admin"  # Set this to the Admin role in your AWS account, this is typically 'Admin'
)
trusted_registries = "602401143452.dkr.ecr.us-east-1.amazonaws.com,busybox"
##########################################################################################################


app = App()
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

NagSuppressions.add_resource_suppressions_by_path(
    config_stack,
    "/configrules/sechub-dl-queue/Resource",[
        {
            "id": "AwsSolutions-SQS3",
            "reason": "Queue does not require DLQ as it is already a DLQ",
        }
    ],
)
Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()


