""" This module contains ec2_proxy class. """


import itertools
import logging
import os
import typing
import uuid


import boto3
import expiringdict


from . import guarded_kv_store


LOGGER = logging.getLogger(__name__)


class ec2_proxy:
    """ This class behaves as proxy for several ec2 boto3 actions.
        
        Responses from the API are cached and stored for some time
            - thanks to that they can be queried by the user later.

        It's thread safe, since it usages guarded_kv_store.
    """

    FLAVORS_FILE = f'{os.path.dirname(os.path.realpath(__file__))}/miscellaneous/flavors.txt'
    REQUESTS_LIMITS = {'max_len': 1000, 'max_age_seconds': 1500}

    def __init__(self, region_name: str = 'us-east-2') -> None:
        self._ec2 = boto3.client('ec2', region_name=region_name)

        self._instances = guarded_kv_store.guarded_kv_store()
        self._images = guarded_kv_store.guarded_kv_store()
        self._flavors = guarded_kv_store.guarded_kv_store()

        # Requests are not kept in the memory for ever.
        #
        # I don't like the idea of creating an interface to delete
        # them, so it has to be done automagically - and the simplest
        # solution is to use expiringdict.
        #
        # Limitations are defined as ec2_proxy.REQUESTS_LIMITS.
        self._requests = guarded_kv_store.guarded_kv_store(
            dict_cls=lambda: expiringdict.ExpiringDict(
                **ec2_proxy.REQUESTS_LIMITS))

        try:
            with open(ec2_proxy.FLAVORS_FILE, 'r') as fh:
                # Flavors are taken from the file shipped with project, because
                # there is no AWS EC2 Api call to retrieve them.
                # 
                # They are not inserted directly to the code either, since there
                # are a lot of them - it would disrupt the vissibility of the code.
                #
                # In case of flavors guarded_kv_store is still used to store them
                #     - it's done just to be consistent with other resources.
                flavors = [flavor.strip() 
                           for flavor in fh.read().splitlines()
                           if flavor.strip()]
                empty_values = itertools.repeat('', len(flavors))
                self._flavors.bulk_insert(entries=list(zip(flavors, empty_values)))
        except FileNotFoundError:
            LOGGER.warning('Failed to load flavors. File does not exist: "%s"',
                           ec2_proxy.FLAVORS_FILE)

        LOGGER.info('Initialization finished! Ready to work :D')


    def get_cached_instances(self) -> typing.List[typing.Dict[str, dict]]:
        """ Return instances that were cached. """
        return self._instances.bulk_get()

    def get_cached_images(self) -> typing.List[typing.Dict[str, dict]]:
        """ Return images that were cached. """
        return self._images.bulk_get()

    def get_cached_flavors(self) -> typing.List[str]:
        """ Return flavors that were cached. """
        return self._flavors.bulk_get().keys()

    def get_cached_requests(self) -> typing.List[typing.Dict[str, dict]]:
        """ Return requests that were cached. """
        return self._requests.bulk_get()

    def run_instances(self, **kwargs) -> dict:
        """ Run run_instances, cache the response, cache created instances,
            and return the response.
        """
        response, status_code = self._run_boto3_method('run_instances', **kwargs)

        if status_code == 200:
            self._instances.bulk_insert(
                (instance['InstanceId'], instance)
                for instance in response['Instances']
            )

        return response

    def describe_instances(self, **kwargs) -> dict:
        """ Run describe_instances, cache the response, cache described instances,
            and return the response.
        """
        response, status_code = self._run_boto3_method('describe_instances', **kwargs)

        if status_code == 200:
            self._instances.bulk_insert(
                (instance['InstanceId'], instance)
                for reservation in response['Reservations']
                for instance in reservation['Instances']
                #if instance[]
            )

        return response

    def terminate_instances(self, **kwargs) -> dict:
        """ Run terminate_instances, cache the response, remove terminated instances from cache,
            and return the response.
        """
        response, status_code = self._run_boto3_method('terminate_instances', **kwargs)

        if status_code == 200:
            instance_ids = [instance['InstanceId']
                            for instance in response['TerminatingInstances']]
            self.describe_instances(InstanceIds=instance_ids)

        return response

    def describe_images(self, **kwargs) -> dict:
        """ Run describe_images, cache the response, cache described images,
            and return the response.
        """
        response, status_code = self._run_boto3_method('describe_images', **kwargs)

        if status_code == 200:
            self._images.bulk_insert(
                (image['ImageId'], image)
                for image in response['Images']
            )

        return response

    def _run_boto3_method(self, method_name: str, **kwargs) -> typing.Tuple[dict, int]:
        """ Run _boto3_method, cache the response and return it. """
        try:
            response = getattr(self._ec2, method_name)(**kwargs)
        except Exception as e:
            response = e.response

        request_id = response['ResponseMetadata']['RequestId']

        self._requests.insert(
            key=request_id,
            value=response
        )

        response_status_code = response['ResponseMetadata']['HTTPStatusCode']

        if response_status_code == 200:
            LOGGER.info('%s succeded / request_id: "%s"',
                        method_name, request_id)
        else:
            LOGGER.error('%s failed with code %d / request_id: "%s"',
                         method_name, response_status_code, request_id)

        return response, response_status_code