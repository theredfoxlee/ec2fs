#!/usr/bin/env python3


import errno
import os
import stat
import time
import typing

import boto3
import moto
import fuse


class _FileAttrs(typing.NamedTuple):
    st_mode: int
    st_nlink: int
    st_size: int
    st_ctime: int
    st_mtime: int
    st_atime: int
    st_uid: int
    st_gid: int


class _QueueFile(typing.NamedTuple):
    attrs: _FileAttrs 
    sqs_url: str
    sqs_attrs: dict


class _Dir(typing.NamedTuple):
    attrs: _FileAttrs
    files: typing.List[str]


class SQSFS(fuse.LoggingMixIn, fuse.Operations):

    def __init__(self, sqs):
        self._uid, self._gid = os.getuid(), os.getgid()
        self._handler = {'/': self._create_dir(mode=0o755)}
        self._sqs = sqs

    def create(self, path, mode):
        queue_url, queue_attrs = self._create_queue(path)
        self._handler[path] = self._create_queue_file(queue_url, queue_attrs, mode)
        dirname, basename = os.path.split(path)
        self._handler[dirname].files.append(basename)
        return 0

    def getattr(self, path, fh=None):
        if path not in self._handler:
            raise fuse.FuseOSError(errno.ENOENT)
        return self._handler[path].attrs._asdict()

    def mkdir(self, path, mode):
        self._handler[path] = self._create_dir(mode)
        dirname, basename = os.path.split(path)
        self._handler[dirname].files.append(basename)

    def readdir(self, path, fh):
        return ['.', '..'] + self._handler[path].files

    def getxattr(self, path, name, position=0):
        try:
            return str(self._handler[path].sqs_attrs[name]).encode()
        except KeyError:
            return ''

    def listxattr(self, path):
        return self._handler[path].sqs_attrs.keys()

    def write(self, path, data, offset, fh):
        if offset != 0:
            raise fuse.FuseOSError(errno.EPERM)
        self._sqs.send_message(QueueUrl=self._handler[path].sqs_url, MessageBody=data.decode())
        return len(data)

    def truncate(self, path, length, fh=None):
        pass

    def read(self, path, size, offset, fh):
        if offset != 0:
            raise fuse.FuseOSError(errno.EPERM)
        size = (size % 10) +  1
        messages = self._sqs.receive_message(QueueUrl=self._handler[path].sqs_url, MaxNumberOfMessages=size)
        return '\n'.join(message['Body'] for message in messages['Messages']).encode()

    def flush(self, path, fh):
        pass

    def _create_queue(self, path):
        # TODO: add check if success
        path = path.lstrip('/')
        queue_url = self._sqs.create_queue(QueueName=path)['QueueUrl']
        queue_attrs = self._sqs.get_queue_attributes(QueueUrl=queue_url)['Attributes']
        queue_attrs['QueueUrl'] = queue_url
        return queue_url, queue_attrs

    def _create_queue_file(self, queue_url, queue_attrs, mode):
        now = time.time()
        attrs = _FileAttrs(
            st_mode=(stat.S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_uid=self._uid,
            st_gid=self._gid
        )
        return _QueueFile(attrs=attrs, sqs_url=queue_url, sqs_attrs=queue_attrs)
    
    def _create_dir(self, mode):
        now = time.time()
        attrs = _FileAttrs(
            st_mode=(stat.S_IFDIR | mode),
            st_nlink=2,
            st_size=4096,
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_uid=self._uid,
            st_gid=self._gid
        )
        return _Dir(attrs=attrs, files=[])


@moto.mock_sqs
def main():
    import argparse
    import logging
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    args = parser.parse_args()
    sqs = boto3.client('sqs', region_name='us-west-1')

    logging.basicConfig(level=logging.DEBUG)
    fuse.FUSE(SQSFS(sqs), args.mount, foreground=True, allow_other=True)


if __name__ == '__main__':
    main()
