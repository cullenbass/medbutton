terraform {
  backend "s3" {
    key = "medbutton"
    region = "us-east-1"
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.82.2"
    }
  }
}

provider "aws" {
  region = "us-east-1"
} 

variable "region" {
  type = string
  default = "us-east-1"
}

variable "prefix" {
  type = string
  description = "Prefix for all resources"
}

variable "phones" {
  type = list(string)
  description = "List of phones to attach"
}

data "archive_file" "lambda" {
  type = "zip"
  source_file = "${path.module}/main.py"
  output_path = "${path.module}/main.zip"
}

resource "aws_iam_role" "role" {
  name = "${var.prefix}-medbutton"
  assume_role_policy = <<-EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}

EOF
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "sns" {
  name = "sns_policy"
  role = aws_iam_role.role.name

  policy = <<-EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "sns:*"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sns_topic.sns.arn}"
    },
    {
      "Action": ["lambda:*"],
      "Effect": "Allow",
      "Resource": "${aws_lambda_function.func.arn}"
    }
  ]
}
EOF

}

resource "aws_lambda_function" "func" {
  filename = "main.zip"
  function_name = "${var.prefix}-medbutton"
  role = aws_iam_role.role.arn
  handler = "main.handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime = "python3.13"
  environment {
    variables = {
      LAST_PUSHED = "0",
      SNS_TOPIC = aws_sns_topic.sns.arn
    }
  }
  lifecycle {
    ignore_changes = [environment]
  }
}

resource "aws_cloudwatch_event_rule" "trigger" {
  name = "${var.prefix}-medbutton"
  description = "Fires every five minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "trigger" {
  rule = aws_cloudwatch_event_rule.trigger.name
  target_id = "lambda"
  arn = aws_lambda_function.func.arn
}

resource "aws_lambda_permission" "cw_perm" {
  statement_id = "AllowExecutionFromCloudWatch"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.func.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.trigger.arn
}

resource "aws_sns_topic" "sns" {
  name = "${var.prefix}-medbutton"
  lifecycle {
    ignore_changes = [
      application_failure_feedback_role_arn,
      application_success_feedback_role_arn,
      http_failure_feedback_role_arn,
      http_success_feedback_role_arn,
      lambda_failure_feedback_role_arn,
      lambda_success_feedback_role_arn,
      sqs_failure_feedback_role_arn,
      sqs_success_feedback_role_arn
    ]
  }
}

resource "aws_sns_topic_subscription" "phone" {
  for_each = toset(var.phones)
  topic_arn = aws_sns_topic.sns.arn
  protocol = "sms"
  endpoint = each.key
}

resource "aws_lambda_function_url" "func" {
  function_name = aws_lambda_function.func.function_name
  authorization_type = "NONE"
}

output "url" {
  value = aws_lambda_function_url.func.function_url
}