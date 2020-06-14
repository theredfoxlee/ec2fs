""" This module contains ec2fs class. """


import errno
import json
import logging
import os
import stat
import time
import typing


import fuse


LOGGER = logging.getLogger(__name__)


class ec2fs(fuse.LoggingMixIn, fuse.Operations):
    """ ec2fs is an communication layer between fs and aws. """

    class dir_entry:

        def __init__(self, mode):
            self.attrs: dict = self._get_dir_attrs(mode=mode)
            self.files: typing.List[str] = []

        def _get_dir_attrs(self, mode):
            now = time.time()
            return {
                'st_mode': stat.S_IFDIR | mode,
                'st_nlink': 2,
                'st_size': 4096,
                'st_ctime': now,
                'st_mtime': now,
                'st_atime': now,
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

    class file_entry:

        def __init__(self, data, mode):
            self.attrs: dict = self._get_file_attrs(size=len(data), 
                                                    mode=mode)
            self.data: bytes = data

        def update_data(self, data: bytes):
            self.data = data
            self.attrs['st_size'] = len(data)

        def _get_file_attrs(self, size, mode):
            now = time.time()
            return {
                'st_mode': stat.S_IFREG | mode,
                'st_nlink': 1,
                'st_size': size,
                'st_ctime': now,
                'st_mtime': now,
                'st_atime': now,
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }


    def __init__(self, ec2: 'ec2fs.ec2_proxy'):
        self._ec2 = ec2

        self._fh = {'/': ec2fs.dir_entry(mode=0o755)}

        self._mkdir('/instances')
        self._mkdir('/images')
        self._mkdir('/actions')

        self._create_file('/actions/run_instances')
        self._create_file('/actions/describe_instances')
        self._create_file('/actions/terminate_instances')
        self._create_file('/actions/describe_images')

        self._create_file('/refresh')
        self._mkdir('/requests')

        #for instance_id, instance in self._ec2.get_cached_instances():
        #    self._create_file(f'/instances/{instance_id}', data=json.dumps(instance))

        #for image_id, image in self._ec2.get_cached_images():
        #    self._create_file(f'/images/{image_id}', data=json.dumps(image))

        #for request_id, request in self._ec2.get_cached_requests():
        #    self._create_file(f'/requests/{request_id}', data=json.dumps(request))

        self._create_file('/flavors', data='\n'.join(
            flavor for flavor in self._ec2.get_cached_flavors()).encode())

    def getattr(self, path: str, fh: int = None) -> None:
        dirname, basename = os.path.split(path)
        if dirname == '/instances':
            try:
                fh = self._ec2.get_cached_instances()[basename]
                return ec2fs.file_entry(data=json.dumps(fh, default=str).encode(), mode=0o755).attrs
            except KeyError:
                raise fuse.FuseOSError(errno.ENOENT)
        elif dirname == '/images':
            try:
                fh = self._ec2.get_cached_images()[basename]
                return ec2fs.file_entry(data=json.dumps(fh, default=str).encode(), mode=0o755).attrs
            except KeyError:
                raise fuse.FuseOSError(errno.ENOENT)
        elif dirname == '/requests':
            try:
                fh = self._ec2.get_cached_requests()[basename]
                return ec2fs.file_entry(data=json.dumps(fh, default=str).encode(), mode=0o755).attrs
            except KeyError:
                raise fuse.FuseOSError(errno.ENOENT)
        elif path not in self._fh:
            raise fuse.FuseOSError(errno.ENOENT)
        return self._fh[path].attrs

    def readdir(self, path: str, fh: int) -> typing.List[str]:
        if path == '/instances':
            return ['.', '..'] + list(self._ec2.get_cached_instances().keys())
        elif path == '/images':
            return ['.', '..'] + list(self._ec2.get_cached_images().keys())
        elif path == '/requests':
            return ['.', '..'] + list(self._ec2.get_cached_requests().keys())
        else:
            return ['.', '..'] + self._fh[path].files

    #def getxattr(self, path: str, name: str, position: int = 0) -> bytes:
    #    try:
    #        return str(self._fh[path].xattrs[name]).encode()
    #    except KeyError:
    #        return ''
    
    #def listxattr(self, path: str) -> typing.List[str]:
    #    return self._fh[path].xattrs.keys()

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        #if fh:
        #    pass
        #    return json.dumps(json.dumps(fh.data), default=str).encode()
        #else:
        dirname, basename = os.path.split(path)
        if dirname == '/instances':
            return json.dumps(self._ec2.get_cached_instances()[basename], default=str).encode()
        elif dirname == '/images':
            return json.dumps(self._ec2.get_cached_images()[basename], default=str).encode()
        elif dirname == '/requests':
            return json.dumps(self._ec2.get_cached_requests()[basename], default=str).encode()
        elif path == '/flavors':
            return self._fh[path].data
        else:
            return json.dumps(self._fh[path].data, default=str).encode()

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        if path == '/refresh':
            self._ec2.describe_instances()
            self._ec2.describe_images()
        else:
            _json = json.loads(data)
            if path == '/actions/run_instances':
                self._ec2.run_instances(**_json)
            elif path == '/actions/describe_instances':
                self._ec2.describe_instances(**_json)
            elif path == '/actions/terminate_instances':
                self._ec2.terminate_instances(**_json)
            elif path == '/actions/describe_images':
                self._ec2.describe_images(**_json)
        return len(data)

    def truncate(self, path: str, length: int, fh: int = None) -> None:
        pass

    def utimens(self, path, times=None):
        pass

    def _mkdir(self, name, mode: int = 0o755):
        dirname, basename = os.path.split(name)
        self._fh[dirname].files.append(basename)
        self._fh[name] = ec2fs.dir_entry(mode=mode)

    def _create_file(self, name:str , data: bytes = b'', mode: int = 0o755):
        dirname, basename = os.path.split(name)
        self._fh[dirname].files.append(basename)
        self._fh[name] = ec2fs.file_entry(data=data, mode=mode)