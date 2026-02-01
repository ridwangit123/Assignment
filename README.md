# Automated Incident Response System

Monitoring and remediation solution for detecting performance degradation in web applications and automatically triggering corrective actions.

## Overview

This solution implements a three part monitoring and automation pipeline:

1. **Sumo Logic Monitoring** - Query and alert configuration for high-latency API requests
2. **Lambda Function** - Event-driven remediation handler for EC2 instance restarts
3. **Infrastructure as Code** - Terraform deployment with least privilege IAM policies

## Implementation

### Sumo Logic Alert (`sumo_logic_query.txt`)
Monitors `/api/data` endpoint response times and triggers when more than 5 requests exceed 3 seconds within a 10-minute window.

### Lambda Handler (`lambda_function/`)
Restart EC2 instances on alert with retry logic and SNS notifications.

### Infrastructure (`terraform/`)

**Deployment:**
```bash
cd terraform
terraform init
terraform apply -var="ami=ami-xxxxxxxxx"
```

**Resources:**
- EC2 instance for application hosting
- SNS topic for operational alerts
- Lambda function with dynamically-scoped IAM permissions



### Testing

Invoke the Lambda function directly:
```bash
aws lambda invoke --function-name restart-ec2-on-sumo \
  --payload '{"message": "Test alert"}' response.json
```