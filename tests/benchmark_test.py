""" This module contains all benchmark tests for ec2fs. """


import json
import os
import logging


# def test_run_images_ec2fs(mocked_ec2fs, benchmark):
#     def run_images():
#         with open(f'{mocked_ec2fs}/actions/run_images', 'w') as fh:
#             json.dump({
#                 'InstanceType': 't2.nano',
#                 'MaxCount': 5,
#                 'MinCount': 5,
#                 'ImageId': 'ami-03cf127a'
#                 }, 
#                 fh
#             )
#     benchmark.pedantic(run_images, iterations=10, rounds=10)


def test_describe_instances_ec2fs(mocked_ec2fs, benchmark):
    with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
        json.dump({
            'InstanceType': 't2.nano',
            'MaxCount': 50,
            'MinCount': 50,
            'ImageId': 'ami-03cf127a'
            }, 
            fh
        )
    def describe_instances():
        with open(f'{mocked_ec2fs}/actions/describe_instances', 'w') as fh:
            json.dump({}, fh)
    benchmark.pedantic(describe_instances, iterations=10, rounds=10)


def test_describe_instances_boto3(mocked_ec2_client, benchmark):
    mocked_ec2_client.run_instances(**{
        'InstanceType': 't2.nano',
        'MaxCount': 50,
        'MinCount': 50,
        'ImageId': 'ami-03cf127a'
    })
    def describe_instances():
        mocked_ec2_client.describe_instances()
    benchmark.pedantic(describe_instances, iterations=10, rounds=10)


def test_cat_instances(mocked_ec2fs, benchmark):
    with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
        json.dump({
            'InstanceType': 't2.nano',
            'MaxCount': 50,
            'MinCount': 50,
            'ImageId': 'ami-03cf127a'
            }, 
            fh
        )
    # with open(f'{mocked_ec2fs}/actions/describe_instances', 'w') as fh:
    #     json.dump({}, fh)
    def describe_instances():
        for instance_id in next(os.walk(f'{mocked_ec2fs}/instances'))[1]:
            with open(f'{mocked_ec2fs}/instances/{instance_id}', 'r') as fh:
                fh.read()
    benchmark.pedantic(describe_instances, iterations=10, rounds=10)


def test_describe_images_ec2fs(mocked_ec2fs, benchmark):
    with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
        json.dump({}, fh)
    def describe_images():
        with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
            json.dump({}, fh)
    benchmark.pedantic(describe_images, iterations=10, rounds=10)


def test_describe_images_boto3(mocked_ec2_client, benchmark):
    def describe_images():
        mocked_ec2_client.describe_images()
    benchmark.pedantic(describe_images, iterations=10, rounds=10)


def test_cat_images(mocked_ec2fs, benchmark):
    with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
        json.dump({}, fh)
    # with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
    #     json.dump({}, fh)
    def describe_images():
        for instance_id in next(os.walk(f'{mocked_ec2fs}/images'))[1]:
            with open(f'{mocked_ec2fs}/images/{instance_id}', 'r') as fh:
                fh.read()
    benchmark.pedantic(describe_images, iterations=10, rounds=10)

# def test_describe_images_ec2fs(mocked_ec2fs, benchmark):
#     def describe_images():
#         with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
#             json.dump({}, fh)
#     benchmark.pedantic(describe_images, iterations=10, rounds=10)


# def test_run_images_boto3(mocked_ec2_client, benchmark):
#     def run_images():
#         mocked_ec2_client.run_images(**{
#             'InstanceType': 't2.nano',
#             'MaxCount': 5,
#             'MinCount': 5,
#             'ImageId': 'ami-03cf127a'
#         })
#     benchmark.pedantic(run_images, iterations=10, rounds=10)


# def test_describe_images_boto3(mocked_ec2_client, benchmark):
#     def describe_images():
#         mocked_ec2_client.describe_images()
#     benchmark.pedantic(describe_images, iterations=10, rounds=10)

# def test_cat_images(mocked_ec2fs, benchmark):
    # with open(f'{mocked_ec2fs}/actions/describe_images', 'w') as fh:
    #     json.dump({}, fh)
#     def describe_images():
#         for image_id in next(os.walk(f'{mocked_ec2fs}/images'))[1]:
#             with open(f'{mocked_ec2fs}/images/{image_id}', 'r') as fh:
#                 fh.read()
#     benchmark.pedantic(describe_images, iterations=10, rounds=10)



# def test_terminate_images(mocked_ec2fs, benchmark):
#     def terminate_images():
#         old_logger_level = logging.getLogger('ec2fs.ec2_proxy').level
#         logging.getLogger('ec2fs.ec2_proxy').setLevel(logging.CRITICAL)
#         with open(f'{mocked_ec2fs}/actions/terminate_images', 'w') as fh:
#             json.dump({'InstanceIds': []}, fh)
#         logging.getLogger('ec2fs.ec2_proxy').setLevel(old_logger_level)
#     benchmark.pedantic(terminate_images, iterations=20, rounds=20)


# def test_run_images_no_fs(mocked_ec2_client, benchmark):
#     def run_images():
#         mocked_ec2_client.run_images(**{
#             'InstanceType': 't2.nano',
#             'MaxCount': 5,
#             'MinCount': 5,
#             'ImageId': 'ami-03cf127a'
#         })
#     benchmark.pedantic(run_images, iterations=20, rounds=20)


# def test_describe_images_no_fs(mocked_ec2_client, benchmark):
#     mocked_ec2_client.run_images(**{
#         'InstanceType': 't2.nano',
#         'MaxCount': 5,
#         'MinCount': 5,
#         'ImageId': 'ami-03cf127a'
#     })
#     def describe_images():
#         mocked_ec2_client.describe_images()
#     benchmark.pedantic(describe_images, iterations=20, rounds=20)


# def test_describe_images_no_fs(mocked_ec2_client, benchmark):
#     def describe_images():
#         mocked_ec2_client.describe_images()
#     benchmark.pedantic(describe_images, iterations=20, rounds=20)


# def test_terminate_images_no_fs(mocked_ec2_client, benchmark):
#     def terminate_images():
#         old_logger_level = logging.getLogger('ec2fs.ec2_proxy').level
#         logging.getLogger('ec2fs.ec2_proxy').setLevel(logging.CRITICAL)
#         mocked_ec2_client.terminate_images(**{
#             'InstanceIds': []
#         })
#         logging.getLogger('ec2fs.ec2_proxy').setLevel(old_logger_level)
#     benchmark.pedantic(terminate_images, iterations=20, rounds=20)