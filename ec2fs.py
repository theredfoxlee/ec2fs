#!/usr/bin/env python3


""" This module is an entrypoint for ec2fs. """


import argparse
import errno
import json
import logging
import os
import stat
import sys
import time
import typing

import boto3
import fuse
import recordclass


class EC2FS(fuse.LoggingMixIn, fuse.Operations):
    """ EC2FS is an communication layer between fs and aws. """
    
    class FsAttributes(recordclass.RecordClass):
        """ FsAttributes stores fs attributes. """ 
        st_mode: int
        st_nlink: int
        st_size: int
        st_ctime: int
        st_mtime: int
        st_atime: int
        st_uid: int
        st_gid: int

    class EC2InstanceFile(recordclass.RecordClass):
        """ EC2InstanceFile stores EC2 Instance attributes. """
        attrs: 'EC2FS.FsAttributes'
        xattrs: dict

    class File(recordclass.RecordClass):
        """ File represents fs regular file. """
        attrs: 'EC2FS.FsAttributes'
        xattrs: dict

    class Directory(recordclass.RecordClass):
        """ Directory represents fs dir. """
        attrs: 'EC2FS.FsAttributes'
        files: typing.List[str]

    def __init__(self, ec2: 'boto3.resources.factory.ec2.ServiceResource') -> None:
        self._ec2 = ec2

        self._uid = os.getuid()
        self._gid = os.getgid()

        self._fh = {'/': self._create_dir(mode=0o755),
                    '/run_instances': self._create_file(mode=0o755)}
        self._fh['/'].files.append('run_instances')

    def getattr(self, path: str, fh: int = None) -> None:
        if path not in self._fh:
            raise fuse.FuseOSError(errno.ENOENT)
        #if isinstance(self._fh[path], EC2FS.EC2InstanceFile):
        #    ret = self._ec2.describe_instances(InstanceIds=[self._fh[path].xattrs['InstanceId']])
        #    self._fh[path].xattrs = ret['Reservations'][0]['Instances'][0]
        return self._fh[path].attrs.__dict__

    def mkdir(self, path: str, mode: int) -> None:
        self._fh[path] = self._create_dir(mode)
        dirname, basename = os.path.split(path)
        self._fh[dirname].files.append(basename)

    def readdir(self, path: str, fh: int) -> typing.List[str]:
        return ['.', '..'] + self._fh[path].files

    def getxattr(self, path: str, name: str, position: int = 0) -> bytes:
        try:
            return str(self._fh[path].xattrs[name]).encode()
        except KeyError:
            return ''

    def listxattr(self, path: str) -> typing.List[str]:
        return self._fh[path].xattrs.keys()

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        return json.dumps(self._fh[path].xattrs,
                          sort_keys=True, default=str).encode()

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        _json = json.loads(data)
        for instance in self._ec2.run_instances(**_json)['Instances']:
            path = f'/{instance["InstanceId"]}'
            self._fh[path] = self._create_ec2_instance_file(0o665, instance)
            dirname, basename = os.path.split(path)
            self._fh[dirname].files.append(basename)
        return len(data)

    def truncate(self, path: str, length: int, fh: int = None) -> None:
        pass

    def _create_ec2_instance_file(self, mode: int, xattrs: dict) -> 'EC2FS.EC2InstanceFile':
        """ Create EC2FS.EC2InstanceFile. """
        timestamp = time.time()
        attrs = EC2FS.FsAttributes(
            st_mode=(stat.S_IFREG | mode),
            st_nlink=2,
            st_size=4096,
            st_ctime=timestamp,
            st_mtime=timestamp,
            st_atime=timestamp,
            st_uid=self._uid,
            st_gid=self._gid)
        return EC2FS.EC2InstanceFile(attrs=attrs, xattrs=xattrs)

    def _create_file(self, mode: int) -> 'EC2FS.File':
        """ Create EC2FS.File entry. """
        timestamp = time.time()
        attrs = EC2FS.FsAttributes(
            st_mode=(stat.S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=timestamp,
            st_mtime=timestamp,
            st_atime=timestamp,
            st_uid=self._uid,
            st_gid=self._gid)
        return EC2FS.File(attrs=attrs, xattrs={})

    def _create_dir(self, mode: int) -> 'EC2FS.Directory':
        """ Create EC2FS.Directory entry. """
        timestamp = time.time()
        attrs = EC2FS.FsAttributes(
            st_mode=(stat.S_IFDIR | mode),
            st_nlink=2,
            st_size=4096,
            st_ctime=timestamp,
            st_mtime=timestamp,
            st_atime=timestamp,
            st_uid=self._uid,
            st_gid=self._gid)
        return EC2FS.Directory(attrs=attrs, files=[])



def _parse_args(args: typing.List[str]) -> argparse.Namespace:
    """ Return parsed args. """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mock', action='store_true', default=False,
                        help='Mock AWS EC2 service using moto framework.')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Turn on debug logging.')
    parser.add_argument('--region-name', default='us-east-2')
    parser.add_argument('mountpoint', help='EC2FS mountpoint empty directory.')
    return parser.parse_args(args)


def _setup_logger(args: argparse.Namespace) -> None:
    """ Prepare basic configuration of logger. """
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


def _mount(args: argparse.Namespace) -> None:
    """ Create and mount EC2FS instance. """
    _setup_logger(args)

    ec2 = boto3.client('ec2', region_name=args.region_name)

    fuse.FUSE(EC2FS(ec2), args.mountpoint,
              foreground=True, allow_other=True)


def main() -> None:
    """ EC2FS entrypoint. """
    args = _parse_args(sys.argv[1:])

    if args.mock:
        import moto
        with moto.mock_ec2():
            _mount(args)
    else:
        _mount(args)
    

if __name__ == '__main__':
    main()