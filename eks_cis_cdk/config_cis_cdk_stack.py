from constructs import Construct
from aws_cdk import (
    aws_config as config,
    aws_lambda as lambda_,
    aws_iam as _iam,
    aws_eks as eks,
    aws_sqs as sqs,
    aws_kms as kms,
    Duration,
    Stack,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from lambda_configs import lambdas as lambdas


class lambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        eks_lambda_role: str,
        eks_cluster: eks.Cluster,
        trusted_registries: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        target_clusters = eks_cluster
        trusted_registries = trusted_registries



        ################## IAM Role for SQS Queue Lambda ############################################################

        # Create role for your Lambda function
        lambda_role = _iam.Role(
            scope=self,
            id="eks-cis-lambda-role",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="cdk-lambda-role",
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "ConfigPutEvaluations": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            effect=_iam.Effect.ALLOW,
                            actions=[
                                "config:DescribeConfigRules",
                                "config:DescribeConfigRuleEvaluationStatus",
                                "securityhub:BatchUpdateFindings",
                                "securityhub:BatchImportFindings",
                            ],
                            resources=["*"],
                        )
                    ]
                )
            },
        )

        ################## SQS Queue ############################################################
        """KMS Key for SQS Queue"""
        sqs_kms = kms.Key(self,"sqs-kms-key",enable_key_rotation=True)

        """Dead Letter Queue for Security Hub findings"""
        sqs_dlq = sqs.Queue(
            self, "sechub-dl-queue", 
            queue_name="sec-hub-deadletter-queue",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=sqs_kms
        )

        """Queue for distributing findings to Security Hub"""
        sqs_queue = sqs.Queue(
            self,
            "sechub-sqs-queue",
            visibility_timeout=Duration.seconds(300),
            queue_name="sec-hub-findings-sqs",
            receive_message_wait_time=Duration.seconds(20),
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=10, queue=sqs_dlq),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=sqs_kms,
        )
        sqs_pol_consume = sqs_queue.grant_consume_messages(lambda_role)
        sqs_pol_send = sqs_queue.add_to_resource_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["sqs:SendMessage"],
                principals=[eks_lambda_role],
                resources=[sqs_queue.queue_arn],
            )
        )

        """Lambda that puts security hub findings"""
        sqs_lambda = lambda_.Function(
            self,
            "sqs-sec-hub-lambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            function_name="sqs_sec-hub_lambda",
            description="lambda that puts security findings from EKS config rules to security hub",
            code=lambda_.Code.from_asset("resources/sechub-lambda"),
            handler="index.lambda_handler",
            role=lambda_role,
            timeout=Duration.seconds(300),
            environment={
                "NAME": "sqs_sec-hub_lambda",
                "sqs_queue": sqs_queue.queue_arn,
                "sqs_queue_url": sqs_queue.queue_url,
            },
        )

        sqs_event_source = sqs_lambda.add_event_source(
            SqsEventSource(
                sqs_queue, batch_size=10, max_batching_window=Duration.minutes(5)
            )
        )



        ################## kubernetes Lambda Layer ############################################################

        # Here define a Lambda Layer
        kubernetes_lambda_layer = lambda_.LayerVersion(
            self,
            "Boto3LambdaLayer",
            code=lambda_.Code.from_asset("resources/kubernetes_layer/"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
        )

        ################## Lambdas and config rules ############################################################
        for function in lambdas["functions"]:
            if lambdas["functions"][function]["name"] == "trustedRegCheck":
                input_parameters = {
                    "inscopeclusters": target_clusters,
                    "trusted_registries": trusted_registries,
                }
            else:
                input_parameters = {"inscopeclusters": target_clusters}
            config_lambda = lambda_.Function(
                self,
                lambdas["functions"][function]["name"],
                runtime=lambda_.Runtime.PYTHON_3_9,
                function_name=lambdas["functions"][function]["name"] + "_lambda",
                description=lambdas["functions"][function]["description"],
                code=lambda_.Code.from_asset(lambdas["functions"][function]["code"]),
                handler="index.lambda_handler",
                role=eks_lambda_role,
                timeout=Duration.seconds(300),
                layers=[kubernetes_lambda_layer],
                environment={
                    "NAME": lambdas["functions"][function]["name"],
                    "sqs_queue": sqs_queue.queue_arn,
                    "sqs_queue_url": sqs_queue.queue_url,
                },
            )

            lambda_configRule = config.CustomRule(
                self,
                "eks-" + lambdas["functions"][function]["name"] + "-rule",
                lambda_function=config_lambda,
                config_rule_name="eks-"
                + lambdas["functions"][function]["name"]
                + "-rule",
                periodic=True,
                description=lambdas["functions"][function]["description"],
                maximum_execution_frequency=config.MaximumExecutionFrequency.ONE_HOUR,
                input_parameters=input_parameters,
            )
