""" This module contains pytest fixtures. """


import boto3
import moto
import pytest


from ec2fs import ec2_proxy


@pytest.fixture
def ec2_mock():
    return moto.mock_ec2()

@pytest.fixture
def not_mocked_ec2_client():
    return boto3.client('ec2', region_name='us-east-2')

@pytest.fixture
def not_mocked_ec2_proxy():
    return ec2_proxy.ec2_proxy()

@pytest.fixture
def mocked_ec2_proxy(ec2_mock):
    ec2_mock.start()
    yield ec2_proxy.ec2_proxy()
    ec2_mock.stop()