from setuptools import setup
from setuptools.command.install import install


import os


def _get_requirements():
    """ Reads requirements.txt located next to setup.py. """
    path = f'{os.path.dirname(os.path.realpath(__file__))}/requirements.txt'
    with open(path, 'r') as fh:
        return fh.read().split()


setup(
    name='ec2fs',
    version='0.1.0',
    description='<description>',
    author='Kamil Janiec',
    author_email='kamil.p.janiec@gmail.com',
    packages=['ec2fs'],
    install_requires=_get_requirements(),
    include_package_data=True
)