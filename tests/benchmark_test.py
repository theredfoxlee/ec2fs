""" This module contains all benchmark tests for ec2fs. """


import json


def test_run_instances(mocked_ec2fs, benchmark):
    def run_instances():
        with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
            json.dump({
                'InstanceType': 't2.nano',
                'MaxCount': 5,
                'MinCount': 5,
                'ImageId': 'ami-03cf127a'
                }, 
                fh
            )
    benchmark.pedantic(run_instances, iterations=10, rounds=10)


def test_describe_instances(mocked_ec2fs, benchmark):
    with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
        json.dump({
            'InstanceType': 't2.nano',
            'MaxCount': 5,
            'MinCount': 5,
            'ImageId': 'ami-03cf127a'
            }, 
            fh
        )
    def describe_instances():
        with open(f'{mocked_ec2fs}/actions/describe_instances', 'w') as fh:
            json.dump({}, fh)
    benchmark.pedantic(describe_instances, iterations=10, rounds=10)


def test_describe_images(mocked_ec2fs, benchmark):
    def describe_images():
        with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
            json.dump({}, fh)
    benchmark.pedantic(describe_images, iterations=10, rounds=10)