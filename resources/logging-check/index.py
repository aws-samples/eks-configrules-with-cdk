"""Checks whether Control Plane logging is enabled for an EKS cluster"""
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
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


def check_cluster_logging(cluster_name):
    try:
        client = boto3.client("eks")
        cluster = client.describe_cluster(name=cluster_name)
        clusterarn = cluster["cluster"]["arn"]
        logcheck = cluster["cluster"]["logging"]["clusterLogging"][0]["enabled"]
        if logcheck == False:
            compliance_type = "NON_COMPLIANT"
            annotation_message = f"{cluster_name} does not have logging enabled, for further information see: https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html"
        elif logcheck == True:
            compliance_type = "COMPLIANT"
            annotation_message = f"{cluster_name} has logging enabled"
        return {
            "compliance_type": compliance_type,
            "annotation": annotation_message,
            "clusterarn": clusterarn,
        }

    except ClientError as e:
        logging.error(f"Issue describing cluster {cluster_name}")
        logging.error(str(e))
        return {
            "compliance_type": "NOT_APPLICABLE",
            "annotation": f"Validation was not run against cluster {cluster_name}, error encountered: {e.response['Error']['Code']}",
        }


def evaluate_compliance(configuration_item):
    logging.info(f"checking for logging on cluster {configuration_item}")
    evaluation_test = check_cluster_logging(configuration_item)
    return evaluation_test


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
                "check security hub",
                invoking_event["notificationCreationTime"],
                event["resultToken"],
            )
    except Exception as e:
        logging.error("Error in compliance check operation")
        logging.error(str(e))
