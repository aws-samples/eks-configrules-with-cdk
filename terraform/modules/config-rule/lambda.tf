resource "aws_lambda_function" "lambda_function" {
  filename      = "lambda_function_payload.zip"
  function_name = var.function_name
  decription = var.function_description
  role          = var.lambda_role_arn
  handler       = "index.lambda_handler"

  # The filebase64sha256() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the base64sha256() function and the file() function:
  # source_code_hash = "${base64sha256(file("lambda_function_payload.zip"))}"
  source_code_hash = filebase64sha256("lambda_function_payload.zip")

  runtime = "python3.9"

  environment {
    variables = {
      NAME = var.function_name
      sqs_queue = var.sqs_queue
      sqs_queue_url = var.sqs_queue_url
    }
  }
  timeout = 300
}