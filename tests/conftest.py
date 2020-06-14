""" This module contains pytest fixtures. """


import logging
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


LOGGER = logging.getLogger(__name__)


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
    # This fixture is such a badass!

    # To gain a controll over spawned background process
    # we have to spawn it on our own.
    pid = os.fork()

    if pid == 0:
        try:
            LOGGER.debug('FUSE started its work!')
            fuse.FUSE(
                ec2fs.ec2fs(mocked_ec2_proxy),
                str(mountpoint),
                foreground=True,
                allow_other=True)
        except Exception as e:
            LOGGER.error('FUSE failed to spawn with exception: %r', e)
            os._exit(1)
        LOGGER.debug('FUSE finished its work!')
        os._exit(0)  # Finish child execution here.

    # FUSE is not be initialized at once - we have to wait.
    while not os.path.exists(f'{mountpoint}/flavors'):
        try:
            os.kill(pid, 0)
        except OSError:
            # FUSE initialization failed, since process
            # terminated before any special file was created.
            _, fuse_exit_status = os.waitpid(pid, 0)
            if fuse_exit_status == 0:
                LOGGER.warning(
                    'FUSE process finished independently with exit_status 0 '
                    '(DUNNO WHAT HAPPEND)')
            raise RuntimeError(
                'FUSE process finished independently with exit_status %d',
                fuse_exit_status)
        time.sleep(0.1)  # Yeah, I know - it's a pure evil, well.. - I'm evil.

    yield mountpoint

    try:
        subprocess.run(
            f'fusermount -u {mountpoint}',
            shell=True,
            capture_output=True,
            check=True)
    except CalledProcessError as e:
        LOGGER.error('Failed to umount FUSE instance at "%s": %s',
                     str(mountpoint), e.stderr.decode())
        os.kill(pid, 9)  # Fuck it, use the force.