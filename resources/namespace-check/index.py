
import authutils as auth
import os
import kubernetes
from kubernetes.client.rest import ApiException
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from botocore import session
from awscli.customizations.eks.get_token import STSClientFactory, TokenGenerator, TOKEN_EXPIRATION_MINS
import traceback
import logging
import json

def check_compliancechange(configrule,current_state):
    try:
        client = boto3.client('config')
        config_status = client.get_compliance_details_by_config_rule(ConfigRuleName=configrule)
        change_compliance_state = False
        if len(config_status['EvaluationResults']) == 0:
            logging.info('no prior evaluation results recorded for rule')
            change_compliance_state == True
        previous_state = config_status['EvaluationResults'][0]['ComplianceType']
        if current_state == previous_state:
            previous_state = config_status['EvaluationResults'][0]['ComplianceType']
            logging.info('Compliance state matches')
            change_compliance_state == False
            return change_compliance_state
        else:
            previous_state = config_status['EvaluationResults'][0]['ComplianceType']
            logging.info(f'Compliance state has changed, previous state was: {previous_state}, current state is: {current_state}')
            change_compliance_state == True
            return change_compliance_state
    except ClientError as e:
        logging.error('issue determining change in compliance')
        logging.error(str(e))



logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(
    format='%(levelname)s %(threadName)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

def evaluate_compliance(configuration_item):
    try:
        token = auth.get_k8s_cluster_token(configuration_item)
        logging.info('Token received')
        endpoint = auth.get_k8s_cluster_endpoint(configuration_item)
        logging.info('Endpoint received')
        k8s_api = auth.initialize_k8s_api(configuration_item, token, endpoint)
        logging.info('K8s API initialized')
        logging.info(f'checking for pods that allow privilege escalation in cluster {configuration_item}')
        evaluation_test = check_default_namespace(k8s_api,cluster_name=configuration_item)
        return evaluation_test
    except Exception as e:
        return str(e)
# def auth.get_k8s_cluster_token(cluster_name):
#     work_session = session.get_session()
#     client_factory = STSClientFactory(work_session)
#     sts_client = client_factory.get_sts_client(role_arn=None)
#     token = TokenGenerator(sts_client).get_token(cluster_name)
#     token_expiration = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINS)
#     expiration = token_expiration.strftime('%Y-%m-%dT%H:%M:%SZ')
#     response = {
#             "kind": "ExecCredential",
#             "apiVersion": "client.authentication.k8s.io/v1alpha1",
#             "spec": {},
#             "status": {
#                 "expirationTimestamp": expiration,
#                 "token": token
#             }
#         }
#     token = response['status']['token']
#     return token


# Check network policy is configured on namespacedef check_pods_default_namespace(k8s_api,cluster_name):
def check_default_namespace(k8s_api,cluster_name):
    try:
        logging.info('checking cluster exists')
        clustercheck = describe_cluster(cluster_name)
        errors = ['ResourceNotFoundException','ClientException','ServerException','ServiceUnavailableException']
        if clustercheck in errors:
            logging.error(f'error {clustercheck} encountered discovering cluster {cluster_name}')
            return {
                "compliance_type": 'NOT_APPLICABLE',
                "annotation": f"Validation was not run against cluster {cluster_name}, error encountered: {clustercheck}"
            }
        else:
            pods = k8s_api.list_pod_for_all_namespaces(watch=False)
            pods_default_namespace = []
            for pod in pods.items:
                if pod.metadata.namespace == 'default':
                    logging.info(f'pod {pod.metadata.name} is running in default namepace')
                    pods_default_namespace.append(pod.metadata.name)
                else:
                    logging.info(f'pod {pod.metadata.name} is compliant, running in namspace {pod.metadata.namespace}')
                if len(pods_default_namespace) > 0:
                    return {
                        "compliance_type": 'NON_COMPLIANT',
                        "annotation": f"Pods: {pods_default_namespace} are running in the default namespace in cluster: {cluster_name}, ensure that pods are not running in the default namespace",
                        "clusterarn": clustercheck
                    }
                elif len(pods_default_namespace) == 0: 
                    return {
                        "compliance_type": 'COMPLIANT',
                        "annotation": f"Cluster: {cluster_name} does not have any pods running in the default namespace",
                        "clusterarn": clustercheck
                    }
                else:
                    return {
                        "compliance_type": 'NOT_APPLICABLE',
                        "annotation": f"Unable to determine status of Cluster: {cluster_name}",
                        "clusterarn": clustercheck
                    }
    except Exception as e:
        logging.error('issue encountered determining network policies on namespace')
        logging.error(e)


'''Validates EKS CLuster exists and obtains ARN'''
def describe_cluster(cluster_name):
    try:
        client = boto3.client('eks')
        cluster = client.describe_cluster(name=cluster_name)
        clusterarn = cluster['cluster']['arn']
        return clusterarn
    except ClientError as e:
        logging.error(f'Issue describing cluster {cluster_name}')
        logging.error(str(e))
        return e.response['Error']['Code']

# def auth.initialize_k8s_api(cluster_name, token, endpoint):
#     configuration = kubernetes.client.Configuration()
#     configuration.api_key['authorization'] = token
#     configuration.api_key_prefix['authorization'] = 'Bearer'
#     configuration.host = endpoint
#     configuration.verify_ssl = False
#     client = kubernetes.client.api_client.ApiClient(configuration)
#     api = kubernetes.client.api.core_v1_api.CoreV1Api(client)
#     return api
    
# def get_k8s_cluster_endpoint(cluster_name):
#     client = boto3.client('eks')
#     response = client.describe_cluster(name=cluster_name)
#     endpoint = response['cluster']['endpoint']
#     return endpoint

def lambda_handler(event, context):
    try:
        logging.info(event)
        # decode the aws confing response
        invoking_event = json.loads(event['invokingEvent'])
        rule_params = json.loads(event['ruleParameters'])
        logging.info(rule_params)
        configuration_items = [rule_params['inscopeclusters']]
        config = boto3.client('config')
        
        logging.info('Setting up connection to EKS cluster')

        for configuration_item in configuration_items:
            logging.info(f'checking compliance for cluster {configuration_item}')
            evaluation = evaluate_compliance(configuration_item)
            logging.info('evaluation result')
            logging.info(evaluation)
            
            logging.info('putting compliance findings')
            try:
                response = config.put_evaluations(
                    Evaluations=[
                        {
                            'ComplianceResourceType': 'AWS::EKS::Cluster',
                            'ComplianceResourceId': evaluation['clusterarn'],
                            'ComplianceType': evaluation['compliance_type'],
                            'Annotation': evaluation['annotation'],
                            'OrderingTimestamp': invoking_event['notificationCreationTime']
                        },
                    ],
                    ResultToken=event['resultToken'])
            except ClientError as e:
                    logging.error('error in putting config check results')
                    logging.error(str(e))
        
    except Exception as e:
        logging.error('Error in compliance check operation')
        logging.error(str(e))
        
    


