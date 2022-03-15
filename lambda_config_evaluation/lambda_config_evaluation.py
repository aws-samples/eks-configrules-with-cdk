import json
import boto3

def lambda_handler(event, context):
    
    client = boto3.client('config')
    response = client.describe_config_rules()
    config_rules = [rule['ConfigRuleName'] for rule in response['ConfigRules']]
    eval = client.start_config_rules_evaluation(
        ConfigRuleNames= config_rules
        )