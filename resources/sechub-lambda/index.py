import boto3
import json
import logging
import hashlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)


def get_description_of_rule(configrule):
    config = boto3.client("config")
    """Gather description of config rule."""
    description = ""
    try:
        response = config.describe_config_rules(ConfigRuleNames=[configrule])
        if "Description" in response["ConfigRules"][0]:
            description = response["ConfigRules"][0]["Description"]
        else:
            description = response["ConfigRules"][0]["ConfigRuleName"]
        return description
    except Exception as error:
        print("Error: ", error)
        raise


def get_compliance_and_severity(new_status):
    """Return compliance status."""
    status = ["FAILED", 3.0, 30]
    if new_status == "COMPLIANT":
        status = ["PASSED", 0, 0]
    return status


def map_config_findings_to_sh(event_details, awsRegion):
    sechub = boto3.client("securityhub")
    """Create custom finding."""
    new_findings = []
    logging.info("more")
    print(event_details)
    print(type(event_details))
    logging.info("logs")
    new_status = event_details["compliance_status"]
    config_rule_name = event_details["configRule"]
    compliance_status = get_compliance_and_severity(new_status)
    description = get_description_of_rule(config_rule_name)
    remediation_url = f"https://console.aws.amazon.com/config/home?region={awsRegion}#/rules/details?configRuleName={config_rule_name}"
    finding_hash = hashlib.sha256(
        f"{event_details['configRuleArn']}-{event_details['resourceId']}".encode()
    ).hexdigest()
    finding_id = f"arn:aws:securityhub:{awsRegion}:{event_details['accountid']}:config/rules/{config_rule_name}/finding/{finding_hash}"
    new_findings.append(
        {
            "SchemaVersion": "2018-10-08",
            "Id": finding_id,
            "ProductArn": (
                f"arn:aws:securityhub:{awsRegion}:"
                f"{event_details['accountid']}:"
                f"product/{event_details['accountid']}/default"
            ),
            "GeneratorId": event_details["configRuleArn"],
            "AwsAccountId": event_details["accountid"],
            "ProductFields": {"ProviderName": "AWS Config"},
            "Types": ["Software and Configuration Checks/AWS Config Analysis"],
            "CreatedAt": event_details["first_recorded_time"],
            "UpdatedAt": (event_details["event_time"]),
            "Severity": {
                "Product": compliance_status[1],
                "Normalized": compliance_status[2],
                "Label": "MEDIUM",
            },
            "Title": config_rule_name,
            "Description": description,
            "Remediation": {
                "Recommendation": {
                    "Text": str(event_details['event_details'])
                    #"Url": remediation_url,
                }
            },
            "UserDefinedFields":{
                "eventdata": str(event_details['event_details'])
            },
            "Resources": [
                {
                    "Id": event_details["resourceId"],
                    "Type": "EKS Cluster",
                    "Partition": "aws",
                    "Region": awsRegion,
                }
            ],
            "Compliance": {"Status": compliance_status[0]},
        }
    )

    try:
        response = sechub.batch_import_findings(Findings=new_findings)
        if response["FailedCount"] > 0:
            print("Failed to import {} findings".format(response["FailedCount"]))
    except Exception as error:
        print("Error: ", error)
        raise


def lambda_handler(event, context):
    print(event)
    payload = json.loads(event["Records"][0]["body"])
    awsRegion = event["Records"][0]["awsRegion"]
    logging.info("adding results to securityhub")
    map_config_findings_to_sh(payload, awsRegion)
