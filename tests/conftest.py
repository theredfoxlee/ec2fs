""" This module contains pytest fixtures. """

import os
import sys
import subprocess
import time
import threading


import boto3
import fuse
import moto
import pytest


from ec2fs import ec2_proxy
from ec2fs import ec2fs


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

@pytest.fixture
def mountpoint(tmpdir):
    return tmpdir

@pytest.fixture
def mocked_ec2fs(mocked_ec2_proxy, mountpoint):
    pid = os.fork()

    if pid == 0:
        fuse.FUSE(
            ec2fs.ec2fs(mocked_ec2_proxy),
            str(mountpoint),
            foreground=True,
            allow_other=True
        )
        # It should not reach this point..
        sys.exit(1)

    while not os.path.exists(f'{mountpoint}/flavors'):
        try:
            os.kill(pid, 0)
        except OSError:
            raise RuntimeError('Failed to spawn ec2fs.')
        time.sleep(1)

    yield mountpoint

    os.kill(pid, 9)
    subprocess.run(f'fusermount -u {mountpoint}', shell=True, check=True)