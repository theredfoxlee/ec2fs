""" This module tests ec2_proxy class. """


import logging


LOGGER = logging.getLogger(__name__)


def test_run_instances(mocked_ec2_proxy):
    instances_len = 5

    response = mocked_ec2_proxy.run_instances(**{
        'InstanceType': 't2.nano',
        'MaxCount': instances_len,
        'MinCount': instances_len,
        'ImageId': 'ami-03cf127a'
    })

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    assert status_code == 200
    assert len(mocked_ec2_proxy.get_cached_instances()) == instances_len
    assert request_id in mocked_ec2_proxy.get_cached_requests()


def test_describe_instances(mocked_ec2_proxy):
    response = mocked_ec2_proxy.describe_instances()

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    assert status_code == 200
    assert request_id in mocked_ec2_proxy.get_cached_requests()
    assert len(mocked_ec2_proxy.get_cached_instances()) == 0


def test_describe_images(mocked_ec2_proxy):
    response = mocked_ec2_proxy.describe_images()

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    assert status_code == 200
    assert request_id in mocked_ec2_proxy.get_cached_requests()
    assert len(mocked_ec2_proxy.get_cached_images()) > 0


def test_terminate_instances(mocked_ec2_proxy):
    mocked_ec2_proxy.run_instances(**{
        'InstanceType': 't2.nano',
        'MaxCount': 1,
        'MinCount': 1,
        'ImageId': 'ami-03cf127a'
    })

    instance_id = list(mocked_ec2_proxy.get_cached_instances().keys())[0]

    response = mocked_ec2_proxy.terminate_instances(**{
        'InstanceIds': [instance_id]
    })

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    assert status_code == 200
    assert request_id in mocked_ec2_proxy.get_cached_requests()

    instance_metadata = mocked_ec2_proxy.get_cached_instances()[instance_id]['data']

    assert 48 == instance_metadata['State']['Code']
    assert 'terminated' == instance_metadata['State']['Name']
    assert 'Client.UserInitiatedShutdown' == instance_metadata['StateReason']['Code']


def test_get_flavors(mocked_ec2_proxy):
    assert len(mocked_ec2_proxy.get_cached_flavors()) > 0

def test_not_available_endpoint(not_mocked_ec2_proxy):
    old_logger_level = logging.getLogger('ec2fs.ec2_proxy').level
    logging.getLogger('ec2fs.ec2_proxy').setLevel(logging.CRITICAL)

    response = not_mocked_ec2_proxy.describe_instances()

    logging.getLogger('ec2fs.ec2_proxy').setLevel(old_logger_level)

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    # boto3 ec2 api returns 401 when there is no AWS to authorize the user

    assert status_code == 401
    assert request_id in not_mocked_ec2_proxy.get_cached_requests()
    assert 'AuthFailure' in response['Error']['Code']


def test_synchronization(ec2_mock, not_mocked_ec2_client, not_mocked_ec2_proxy):
    ec2_mock.start()

    instances_len = 5

    not_mocked_ec2_client.run_instances(**{
        'InstanceType': 't2.nano',
        'MaxCount': instances_len,
        'MinCount': instances_len,
        'ImageId': 'ami-03cf127a'
    })

    assert len(not_mocked_ec2_proxy.get_cached_instances()) == 0

    response = not_mocked_ec2_proxy.describe_instances()

    request_id = response['ResponseMetadata']['RequestId']
    status_code = response['ResponseMetadata']['HTTPStatusCode']

    assert status_code == 200
    assert request_id in not_mocked_ec2_proxy.get_cached_requests()
    assert len(not_mocked_ec2_proxy.get_cached_instances()) == instances_len

    ec2_mock.stop()