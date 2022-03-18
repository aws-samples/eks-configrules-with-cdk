# import aws_cdk as cdk
# from aws_cdk import Stack
# from aws_cdk import assertions
# from aws_cdk.assertions import Template
# from aws_cdk.assertions import Match
# from eks_cis_cdk.config_cis_cdk_stack import lambdaStack
# from eks_cis_cdk.eks_cis_cdk_stack import CdkConfigEksStack 


# app = cdk.App()
# eks_stack = CdkConfigEksStack(
#     app, "eksconfigexample", eks_admin_rolename='Admin'
# )

# '''Define some registries '''
# trusted_registries = "111111111111.dkr.ecr.us-east-1.amazonaws.com,busybox"



# def test_iam_roles():
#     app = cdk.App()
#     config_stack = lambdaStack(
#         app,
#         "configrules",
#         eks_lambda_role=eks_stack.lambda_role,
#         eks_cluster=eks_stack.cluster.cluster_name,
#         trusted_registries=trusted_registries,
#     )
#     template = assertions.Template.from_stack(config_stack)
#     template.resource_count_is("AWS::IAM::Role", 1)

# '''Test KMS Key should be created'''

# def test_key_roles():
#     app = cdk.App()
#     config_stack = lambdaStack(
#         app,
#         "configrules",
#         eks_lambda_role=eks_stack.lambda_role,
#         eks_cluster=eks_stack.cluster.cluster_name,
#         trusted_registries=trusted_registries,
#     )
#     template = assertions.Template.from_stack(config_stack)
#     template.resource_count_is("AWS::KMS::Key", 1)