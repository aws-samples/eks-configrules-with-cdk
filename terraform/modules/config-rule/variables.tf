variable "function_name" {
    type = String
    description = "Name of the Lamdba function to be deployed"
}

variable "lambda_role_arn" {
    type = String
    description = "IAM Role ARN used for the Lamdba Execution Role"
}

variable "sqs_queue" {
    type = String
    description = "SQS Queue ARN to pass config evaluation results to security hub"
}

variable "function_description" {
    type = String
    description = "Description of the function"
}

variable "sqs_queue_url" {
    type = String
    description = "SQS Queue ARN to pass config evaluation results to security hub"
}



