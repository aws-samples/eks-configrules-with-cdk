"""checks Kubernetes cluster for pods that have privilege escalation enabled"""
import authutils as auth
from distutils.command.clean import clean
import os
import kubernetes
from kubernetes.client.rest import ApiException
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from botocore import session
from awscli.customizations.eks.get_token import (
    STSClientFactory,
    TokenGenerator,
    TOKEN_EXPIRATION_MINS,
)
import traceback
import logging
import json
from dateutil.tz import tzlocal

sqs_queue_url = os.environ["sqs_queue_url"]


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

"""evaluates status of cluster against config rule"""


def evaluate_compliance(configuration_item):
    token = auth.get_k8s_cluster_token(configuration_item)
    logging.info("Token received")
    endpoint = auth.get_k8s_cluster_endpoint(configuration_item)
    logging.info("Endpoint received")
    k8s_api = auth.initialize_k8s_api(configuration_item, token, endpoint)
    logging.info("K8s API initialized")
    logging.info(
        f"checking for pods that allow privilege escalation in cluster {configuration_item}"
    )
    evaluation_test = get_pods_allowescalation(k8s_api, configuration_item)
    return evaluation_test


"""Puts config evaluation results"""


def put_evaluations(
    clusterarn, compliance_type, annotation, invoking_event, result_token
):
    client = boto3.client("config")
    try:
        response = client.put_evaluations(
            Evaluations=[
                {
                    "ComplianceResourceType": "AWS::EKS::Cluster",
                    "ComplianceResourceId": clusterarn,
                    "ComplianceType": compliance_type,
                    "Annotation": annotation,
                    "OrderingTimestamp": invoking_event,
                },
            ],
            ResultToken=result_token,
        )
    except ClientError as e:
        logging.error("error in putting config check results")
        logging.error(str(e))


"""evaluates whether compliance status has changed since last evaluation"""


def check_compliancechange(configrule, current_state):
    try:
        client = boto3.client("config")
        config_status = client.get_compliance_details_by_config_rule(
            ConfigRuleName=configrule
        )
        if len(config_status["EvaluationResults"]) == 0:
            logging.info("evaluation has not been run before")
            change_compliance_state = True
            return change_compliance_state

        previous_state = config_status["EvaluationResults"][0]["ComplianceType"]
        change_compliance_state = False
        if current_state == previous_state:
            logging.info("Compliance state matches")
            change_compliance_state = False
            return change_compliance_state
        else:
            logging.info(
                f"Compliance state has changed, previous state was: {previous_state}, current state is: {current_state}"
            )
            change_compliance_state = True
            return change_compliance_state
    except ClientError as e:
        logging.error("issue determining change in compliance ")
        logging.error(str(e))


# """obtains session token for k8s cluster"""


# def get_k8s_cluster_token(cluster_name):
#     work_session = session.get_session()
#     client_factory = STSClientFactory(work_session)
#     sts_client = client_factory.get_sts_client(role_arn=None)
#     token = TokenGenerator(sts_client).get_token(cluster_name)
#     token_expiration = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINS)
#     expiration = token_expiration.strftime("%Y-%m-%dT%H:%M:%SZ")
#     response = {
#         "kind": "ExecCredential",
#         "apiVersion": "client.authentication.k8s.io/v1alpha1",
#         "spec": {},
#         "status": {"expirationTimestamp": expiration, "token": token},
#     }
#     token = response["status"]["token"]
#     return token


"""obtains pods that have containers with privescalation enabled"""


def get_pods_allowescalation(k8s_api, cluster_name):
    logging.info("checking cluster exists")
    clustercheck = describe_cluster(cluster_name)
    errors = [
        "ResourceNotFoundException",
        "ClientException",
        "ServerException",
        "ServiceUnavailableException",
    ]
    if clustercheck in errors:
        logging.error(
            f"error {clustercheck} encountered discovering cluster {cluster_name}"
        )
        return {
            "compliance_type": "NOT_APPLICABLE",
            "annotation": f"Validation was not run against cluster {cluster_name}, error encountered: {clustercheck}",
        }
    response = k8s_api.list_pod_for_all_namespaces(watch=False)
    noncompliantpods = []
    for pod in response.items:
        for i in pod.spec.containers:
            logging.info(f"checking pod {i.name}")
            if str(i.security_context) == "None":
                logger.info(
                    f"pod {i.name} does not have security context configured, skipping"
                )
                break
            else:
                sec_context = i.security_context.__dict__
                if sec_context["_allow_privilege_escalation"] == True:
                    logging.info(f"pod {i.name} allows escalation")
                    noncompliantpods.append(i.name)
                else:
                    logging.info(f"pod {i.name} does not allow escalation")
    if len(noncompliantpods) > 0:
        compliance_type = "NON_COMPLIANT"
        annotation_message = f"Pods: {noncompliantpods} in cluster {cluster_name} have privilege escalation enabled, see https://kubernetes.io/docs/concepts/security/pod-security-standards/ for more details"
    else:
        compliance_type = "COMPLIANT"
        annotation_message = (
            f"No pods in cluster {cluster_name} have privilege escalation enabled "
        )
    logging.info(noncompliantpods)
    return {
        "compliance_type": compliance_type,
        "annotation": annotation_message,
        "clusterarn": clustercheck,
    }


def describe_cluster(cluster_name):
    try:
        client = boto3.client("eks")
        cluster = client.describe_cluster(name=cluster_name)
        clusterarn = cluster["cluster"]["arn"]
        return clusterarn
    except ClientError as e:
        logging.error(f"Issue describing cluster {cluster_name}")
        logging.error(str(e))
        return e.response["Error"]["Code"]


def sqs_put_message(
    sqs_queue_url,
    configrulearn,
    configrule,
    accountid,
    event_details,
    compliance_status,
    first_recorded_time,
    event_time,
    resourceId,
):
    try:
        client = boto3.client("sqs")
        message = {
            "configRuleArn": configrulearn,
            "configRule": configrule,
            "accountid": accountid,
            "event_details": event_details,
            "compliance_status": compliance_status,
            "first_recorded_time": first_recorded_time,
            "event_time": event_time,
            "resourceId": resourceId,
        }
        QueueUrl = (sqs_queue_url,)
        response = client.send_message(
            QueueUrl=sqs_queue_url, MessageBody=json.dumps(message)
        )

    except ClientError as e:
        logging.error(f"issue sending message to sqs queue {sqs_queue_url}")
        logging.error(str(e))


# """initializes the k8s api with the session token"""


# def initialize_k8s_api(cluster_name, token, endpoint):
#     try:
#         configuration = kubernetes.client.Configuration()
#         configuration.api_key["authorization"] = token
#         configuration.api_key_prefix["authorization"] = "Bearer"
#         configuration.host = endpoint
#         configuration.verify_ssl = False
#         client = kubernetes.client.api_client.ApiClient(configuration)
#         api = kubernetes.client.api.core_v1_api.CoreV1Api(client)
#         return api
#     except Exception as e:
#         logging.error(f'Error initialising Kubernetes API for {cluster_name}')
#         return str(e)


"""obtain last run status for config rule to pass to SQS"""


def get_config_evaldetails(configrule):
    try:
        client = boto3.client("config")
        response = client.describe_config_rule_evaluation_status(
            ConfigRuleNames=[configrule]
        )
        if "LastSuccessfulEvaluationTime" in response["ConfigRulesEvaluationStatus"][0]:
            last_eval_time = response["ConfigRulesEvaluationStatus"][0][
                "LastSuccessfulEvaluationTime"
            ]
            logging.info("converting to normal datetime format")
        else:
            last_eval_time = "Null"
        return str(last_eval_time)
    except ClientError as e:
        logging.error("problem obtaining last_eval_time for configrule")
        logging.error(str(e))


"""obtains cluster endpoint"""


# def get_k8s_cluster_endpoint(cluster_name):
#     try:
#         client = boto3.client("eks")
#         response = client.describe_cluster(name=cluster_name)
#         endpoint = response["cluster"]["endpoint"]
#         return endpoint
#     except ClientError as e:
#         logging.error(f'error encountered obtaining cluster endpoint for cluster {cluster_name}')
#         return e.response['Error']['Code']

def lambda_handler(event, context):
    try:
        logging.info(event)
        # decode the aws confing response
        invoking_event = json.loads(event["invokingEvent"])
        rule_params = json.loads(event["ruleParameters"])
        logging.info(rule_params)
        configuration_items = [rule_params["inscopeclusters"]]
        config = boto3.client("config")
        accountid = event["accountId"]
        logging.info("Setting up connection to EKS cluster")

        for configuration_item in configuration_items:
            logging.info(f"checking compliance for cluster {configuration_item}")
            evaluation = evaluate_compliance(configuration_item)
            logging.info("evaluation result")
            logging.info(evaluation)
            logging.info("checking for change in compliance state")
            logging.info(f"event name is {event['configRuleName']}")
            compliance_state_change = check_compliancechange(
                event["configRuleName"], evaluation["compliance_type"]
            )
            logging.info(f"compliance state change: {compliance_state_change}")
            if compliance_state_change == True:
                logging.info(
                    "Compliance state has changed since last evaluation, adding evaluation metadata to sqs queue to import findings into Security Hub"
                )
                last_eval_time = get_config_evaldetails(event["configRuleName"])
                if last_eval_time == "Null":
                    logging.info(
                        f"Evaluation never completed for config rule {event['configRuleName']} before"
                    )
                    last_eval_time = invoking_event["notificationCreationTime"]
                sqs_put_message(
                    sqs_queue_url,
                    event["configRuleArn"],
                    event["configRuleName"],
                    accountid,
                    evaluation["annotation"],
                    evaluation["compliance_type"],
                    last_eval_time,
                    invoking_event["notificationCreationTime"],
                    evaluation["clusterarn"],
                )
            else:
                logging.info("No changes in compliance state since last evaluation")
            logging.info("putting compliance findings")
            put_evaluations(
                evaluation["clusterarn"],
                evaluation["compliance_type"],
                f"Cluster {evaluation['clusterarn']} has pods with privilege escalation enabled, check Security Hub findings for non-compliant pods",
                invoking_event["notificationCreationTime"],
                event["resultToken"],
            )
    except Exception as e:
        logging.error("Error in compliance check operation")
        logging.error(str(e))
