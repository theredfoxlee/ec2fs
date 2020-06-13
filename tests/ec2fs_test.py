
import os
import logging
import json

LOGGER = logging.getLogger(__name__)

def test_ec2fs(mocked_ec2fs):

	with open(f'{mocked_ec2fs}/actions/run_instances', 'w') as fh:
		json.dump({
        'InstanceType': 't2.nano',
        'MaxCount': 5,
        'MinCount': 5,
        'ImageId': 'ami-03cf127a'
    	}, fh)

	_, _, files = next(os.walk(f'{mocked_ec2fs}/instances'))

	for file in files:
		with open(f'{mocked_ec2fs}/instances/{file}', 'r') as fh:
			_json = json.load(fh)
			LOGGER.critical("%s: %r", f'{mocked_ec2fs}/instances/{file}', _json)

	assert True