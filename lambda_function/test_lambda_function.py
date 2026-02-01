import os
import json
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError


def make_mock_clients(reboot_side_effect=None, publish_side_effect=None):
    ec2 = Mock()
    sns = Mock()
    ec2.reboot_instances.side_effect = reboot_side_effect or (lambda **kw: {})
    sns.publish.side_effect = publish_side_effect or (lambda **kw: {"MessageId": "123"})
    return ec2, sns


def test_handler_success(monkeypatch):
    monkeypatch.setenv("EC2_INSTANCE_ID", "i-0123456789abcdef0")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:topic")

    # Import after setting env vars so module reads config at runtime
    import lambda_function.lambda_function as lf

    ec2, sns = make_mock_clients()
    lf._ec2_client = ec2
    lf._sns_client = sns

    event = {"message": "test-reboot"}
    result = lf.handler(event, None)

    assert result["statusCode"] == 200
    ec2.reboot_instances.assert_called_once_with(InstanceIds=["i-0123456789abcdef0"])
    sns.publish.assert_called_once()


def test_handler_missing_env(monkeypatch):
    # Ensure missing EC2_INSTANCE_ID results in 400
    monkeypatch.delenv("EC2_INSTANCE_ID", raising=False)
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:topic")

    import importlib
    import importlib
    import lambda_function.lambda_function as lf

    result = lf.handler({}, None)
    assert result["statusCode"] == 400


def test_handler_client_error(monkeypatch):
    monkeypatch.setenv("EC2_INSTANCE_ID", "i-0123456789abcdef0")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:topic")

    import lambda_function.lambda_function as lf

    ec2 = Mock()
    error_response = {"Error": {"Message": "Fail"}}
    ec2.reboot_instances.side_effect = ClientError(error_response, "RebootInstances")

    lf._ec2_client = ec2
    lf._sns_client = Mock()

    result = lf.handler({}, None)
    assert result["statusCode"] == 502
