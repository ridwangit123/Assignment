terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_sns_topic" "alerts" {
  name = "pacerpro-alerts"
}

resource "aws_instance" "app" {
  ami           = var.ami
  instance_type = var.instance_type
  tags = {
    Name = "pacerpro-app"
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "pacerpro-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "pacerpro-lambda-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:RebootInstances",
      "ec2:DescribeInstances"
    ]
    resources = [aws_instance.app.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]
    resources = [aws_sns_topic.alerts.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${var.region}:*:*"]
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_function"
  output_path = "${path.module}/lambda_package.zip"
}

resource "aws_lambda_function" "restart_ec2" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "restart-ec2-on-sumo"
  handler          = "lambda_function.handler"
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      EC2_INSTANCE_ID = aws_instance.app.id
      SNS_TOPIC_ARN   = aws_sns_topic.alerts.arn
    }
  }
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "lambda_arn" {
  value = aws_lambda_function.restart_ec2.arn
}

output "instance_id" {
  value = aws_instance.app.id
}