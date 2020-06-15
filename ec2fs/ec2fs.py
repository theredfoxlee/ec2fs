""" This module contains ec2fs class. """

import abc
import errno
import json
import logging
import os
import stat
import time
import typing


import fuse
from readerwriterlock import rwlock


LOGGER = logging.getLogger(__name__)


class ec2fs(fuse.LoggingMixIn, fuse.Operations):
    """ ec2fs i a simple filesystem interface for AWS EC2 service. """

    def __init__(self, ec2_proxy: 'ec2fs.ec2_proxy') -> None:
        self._ec2_proxy = ec2_proxy

        flavors_data = '\n'.join(flavor for flavor in self._ec2_proxy.get_cached_flavors() if flavor)
        flavors_data = flavors_data.encode()

        #LOGGER.critical('flavors: %r', flavors_data)

        flavors_attrs = ec2fs._file_attrs_factory()
        flavors_attrs['st_size'] = len(flavors_data)

        self._fh = {
            '/': {
                'attrs': ec2fs._dir_attrs_factory(),
                'files': ['instances', 'images', 'requests', 'flavors', 'actions', 'refresh'],
            },
            '/instances': {
                'attrs': ec2fs._dir_attrs_factory(),
                'files_callback': lambda: list(self._ec2_proxy.get_cached_instances().keys())
            },
            '/images': {
                'attrs': ec2fs._dir_attrs_factory(),
                'files_callback': lambda: list(self._ec2_proxy.get_cached_images().keys())
            },
            '/requests': {
                'attrs': ec2fs._dir_attrs_factory(),
                'files_callback': lambda: list(self._ec2_proxy.get_cached_requests().keys())
            },
            '/flavors': {
                'attrs': flavors_attrs,
                'raw_data': flavors_data,
                'write_callback': None
            },
            '/actions': {
                'attrs': ec2fs._dir_attrs_factory(),
                'files': ['run_instances', 'describe_instances', 'terminate_instances', 'describe_images']
            },
            '/actions/run_instances': {
                'attrs': ec2fs._file_attrs_factory(),
                'raw_data': b'',
                'write_callback': lambda d: self._ec2_proxy.run_instances(**d)
            },
            '/actions/describe_instances': {
                'attrs': ec2fs._file_attrs_factory(),
                'raw_data': b'',
                'write_callback': lambda d: self._ec2_proxy.describe_instances(**d)
            },
            '/actions/terminate_instances': {
                'attrs': ec2fs._file_attrs_factory(),
                'raw_data': b'',
                'write_callback': lambda d: self._ec2_proxy.terminate_instances(**d)
            },
            '/actions/describe_images': {
                'attrs': ec2fs._file_attrs_factory(),
                'raw_data': b'',
                'write_callback': lambda d: self._ec2_proxy.describe_images(**d)
            },
            '/refresh': {
                'attrs': ec2fs._file_attrs_factory(),
                'raw_data': b'',
                'write_callback': lambda: self._ec2_proxy.describe_instances()
            }
        }

    def getattr(self, path: str, fh: int = None) -> dict:
        LOGGER.debug('getattr: %r', path)
        resource = self._get_resource(path)
        if resource:
            resource_attrs = ec2fs._file_attrs_factory()
            resource_attrs['st_size'] = resource['metadata']['size']
            resource_attrs['st_ctime'] = resource['metadata']['@timestamp']
            resource_attrs['st_mtime'] = resource['metadata']['@timestamp']
            resource_attrs['st_atime'] = resource['metadata']['@timestamp']
            return resource_attrs
        elif path in self._fh:
            return self._fh[path]['attrs']
        else:
            raise fuse.FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh: int) -> typing.List[str]:
        LOGGER.debug('readdir: %r', path)
        if 'files_callback' in self._fh[path]:
            return ['.', '..'] + self._fh[path]['files_callback']()
        else:
            return ['.', '..'] + self._fh[path]['files']

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        LOGGER.debug('read: %r', path)
        resource = self._get_resource(path)
        if resource:
            return resource['raw_data'][offset:offset+size]
        else:
            return self._fh[path]['raw_data'][offset:offset+size]

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        LOGGER.debug('write: %r', path)
        write_callback = self._fh[path]['write_callback']
        if write_callback:
            write_callback(json.loads(data))
        else:
            LOGGER.warning('Writing to "%s" has no effect.', path)
        return len(data)

    def truncate(self, path: str, length: int, fh: int = None) -> None:
        pass

    def _get_resource(self, path: str) -> typing.Optional[dict]:
        dirname, basename = os.path.split(path)
        try:
            if dirname == '/instances':
                return self._ec2_proxy.get_cached_instance(basename)
            elif dirname == '/images':
                return self._ec2_proxy.get_cached_image(basename)
            elif dirname == '/requests':
                return self._ec2_proxy.get_cached_request(basename)
            else:
                return None
        except KeyError:
            LOGGER.error('File missing from cache: %s', path)
            raise fuse.FuseOSError(errno.ENOENT)

    @staticmethod
    def _attrs_factory(st_mode: int, st_nlink: int, st_size: int) -> dict:
        now = time.time()
        attrs = {
            'st_mode': st_mode,
            'st_nlink': st_nlink,
            'st_size': st_size,
            'st_ctime': now,
            'st_mtime': now,
            'st_atime': now,
            'st_uid': os.getuid(),
            'st_gid': os.getgid()
        }
        return attrs

    @staticmethod
    def _dir_attrs_factory():
        return ec2fs._attrs_factory(
            st_mode=stat.S_IFDIR | 0o755,
            st_nlink=2,
            st_size=4096
        )

    @staticmethod
    def _file_attrs_factory():
        return ec2fs._attrs_factory(
            st_mode=stat.S_IFREG| 0o755,
            st_nlink=1,
            st_size=0
        )