#!/usr/bin/env python3

from aws_cdk import App, Aspects
from eks_cis_cdk.eks_cis_cdk_stack import CdkConfigEksStack
from eks_cis_cdk.config_cis_cdk_stack import lambdaStack
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from cdknagexemptions import config_rules_by_path as nag_exemptions

# from config_cis_cdk.eks_cis_cdk_stack import lambdaStack
# from eks_cis_cdk.eks_test_stack import lambdaTestStack

############### Deployment Parameters ####################################################################
eks_admin_rolename = (
    "Admin"  # Set this to the Admin role in your AWS account, this is typically 'Admin'
)
trusted_registries = "111111111111.dkr.ecr.us-east-1.amazonaws.com,busybox"
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

# See cdknagexemptions.py for exemption configuration
for exemption in nag_exemptions:
    stack = nag_exemptions["Rules"][exemption]["stack"]
    path = nag_exemptions["Rules"][exemption]["path"]
    rule = nag_exemptions["Rules"][exemption]["path"]
    NagSuppressions.add_stack_suppression_by_path(stack,path,rule)


Aspects.of(app).add(AwsSolutionsChecks())
app.synth()


