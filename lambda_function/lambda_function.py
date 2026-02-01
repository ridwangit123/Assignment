import os
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# Configuration
RETRY_ATTEMPTS = int(os.environ.get("RETRY_ATTEMPTS", "3"))
BACKOFF_BASE_SECONDS = float(os.environ.get("BACKOFF_BASE_SECONDS", "0.5"))

# Reuse clients across invocations
_ec2_client = boto3.client("ec2")
_sns_client = boto3.client("sns")


def _get_config() -> Tuple[str, str]:
    """Get instance_id and topic_arn from environment."""
    instance_id = os.environ.get("EC2_INSTANCE_ID")
    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if not instance_id:
        raise LambdaError("EC2_INSTANCE_ID not set")
    if not topic_arn:
        raise LambdaError("SNS_TOPIC_ARN not set")
    if not str(instance_id).startswith("i-"):
        logger.warning("EC2_INSTANCE_ID does not look like an instance id: %s", instance_id)
    return instance_id, topic_arn


class LambdaError(Exception):
    """Custom exception type for Lambda errors."""


def _parse_alert_summary(event: Any) -> str:
    """Extract alert summary from event payload."""
    default = "Triggered by alert"
    if not isinstance(event, dict):
        return default

    message = event.get("message")
    if message:
        return str(message)

    body = event.get("body")
    if not body:
        return default

    if isinstance(body, str):
        try:
            parsed = json.loads(body)
            return str(parsed.get("message") or parsed.get("summary") or default)
        except json.JSONDecodeError:
            return body

    return str(body)


def _retryable_call(func, attempts: int = RETRY_ATTEMPTS, backoff_base: float = BACKOFF_BASE_SECONDS, **kwargs):
    """Retry with exponential backoff."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return func(**kwargs)
        except ClientError as e:
            last_exc = e
            logger.warning("ClientError on attempt %s/%s: %s", attempt, attempts, e)
            if attempt == attempts:
                break
            sleep_time = backoff_base * (2 ** (attempt - 1))
            time.sleep(sleep_time)
        except Exception as e:
            logger.exception("Non-retryable exception: %s", e)
            raise
    raise last_exc or LambdaError("Retry attempts exhausted")




def _reboot_instance(instance_id: str) -> Dict[str, Any]:
    logger.info("Attempting reboot for instance=%s", instance_id)
    return _retryable_call(_ec2_client.reboot_instances, InstanceIds=[instance_id])


def _publish_sns(topic_arn: str, message: str, subject: str) -> Dict[str, Any]:
    logger.info("Publishing SNS message to %s", topic_arn)
    return _retryable_call(_sns_client.publish, TopicArn=topic_arn, Message=message, Subject=subject)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda entrypoint."""
    logger.info("Handler invoked")
    try:
        instance_id, topic_arn = _get_config()

        alert_summary = _parse_alert_summary(event)

        _reboot_instance(instance_id)

        message = (
            f"Reboot initiated for instance {instance_id}. Reason: {alert_summary}"
        )
        _publish_sns(topic_arn, message=message, subject="EC2 Rebooted")

        logger.info("Operation successful for instance=%s", instance_id)
        return {"statusCode": 200, "body": "Reboot initiated and notification sent."}

    except LambdaError as e:
        logger.error("Configuration or validation error: %s", e)
        return {"statusCode": 400, "body": str(e)}
    except ClientError as e:
        logger.exception("AWS ClientError: %s", e)
        return {"statusCode": 502, "body": str(e)}
    except Exception as e:
        logger.exception("Unhandled exception: %s", e)
        return {"statusCode": 500, "body": "Internal error"}
