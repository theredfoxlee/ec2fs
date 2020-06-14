""" This module tests ec2fs class over FUSE interface. """


import logging
import os
import json


import pytest


LOGGER = logging.getLogger(__name__)


def test_run_instances(mocked_ec2fs):
    instances_len = 5

    assert os.path.isfile(f'{mocked_ec2fs}/actions/run_instances')

    with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
        json.dump({
            'InstanceType': 't2.nano',
            'MaxCount': instances_len,
            'MinCount': instances_len,
            'ImageId': 'ami-03cf127a'
            }, 
            fh
        )

    _, _, instances_files = next(os.walk(f'{mocked_ec2fs}/instances'))
    _, _, requests_files = next(os.walk(f'{mocked_ec2fs}/requests'))

    assert len(instances_files) == instances_len
    assert len(requests_files) == 1


def test_describe_instances(mocked_ec2fs):
    assert os.path.isfile(f'{mocked_ec2fs}/actions/describe_instances')

    with open(f'{mocked_ec2fs}/actions/describe_instances', 'w') as fh:
        json.dump({}, fh)

    _, _, instances_files = next(os.walk(f'{mocked_ec2fs}/instances'))
    _, _, requests_files = next(os.walk(f'{mocked_ec2fs}/requests'))

    assert len(instances_files) == 0
    assert len(requests_files) == 1


def test_describe_images(mocked_ec2fs):
    assert os.path.isfile(f'{mocked_ec2fs}/actions/describe_images')

    with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
        json.dump({}, fh)

    _, _, images_files = next(os.walk(f'{mocked_ec2fs}/images'))
    _, _, requests_files = next(os.walk(f'{mocked_ec2fs}/requests'))

    assert len(images_files) > 0
    assert len(requests_files) == 1


def test_flavors_file(mocked_ec2fs):
    assert os.path.isfile(f'{mocked_ec2fs}/flavors')

    with open(f'{mocked_ec2fs}/flavors', 'r') as fh:
        assert len(fh.read().splitlines()) == 307


def test_terminate_instances(mocked_ec2fs):
    assert os.path.isfile(f'{mocked_ec2fs}/actions/terminate_instances')

    with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
        json.dump({
            'InstanceType': 't2.nano',
            'MaxCount': 1,
            'MinCount': 1,
            'ImageId': 'ami-03cf127a'
            }, 
            fh
        )
    _, _, instances_files = next(os.walk(f'{mocked_ec2fs}/instances'))

    with open(f'{mocked_ec2fs}/actions/terminate_instances', 'w') as fh:
        json.dump({'InstanceIds': instances_files}, fh)

    _, _, instances_files = next(os.walk(f'{mocked_ec2fs}/instances'))

    for instance_id in instances_files:
        with open(f'{mocked_ec2fs}/instances/{instance_id}', 'r') as fh:
            instance_metadata = json.load(fh)

            assert 48 == instance_metadata['State']['Code']
            assert 'terminated' == instance_metadata['State']['Name']
            assert 'Client.UserInitiatedShutdown' == instance_metadata['StateReason']['Code']