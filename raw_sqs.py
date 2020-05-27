#!/usr/bin/env python3

import boto3
import moto


@moto.mock_sqs
def main():
    sqs = boto3.client('sqs', region_name='us-west-1')
    
    test_queue_name = 'test-queue-1'
    sqs.create_queue(QueueName=test_queue_name)

    #queues = sqs.list_queues(QueueNamePrefix=test_queue_name)
    #test_queue_url = queues['QueueUrls'][0]

    test_queue_url = sqs.get_queue_url(QueueName=test_queue_name)['QueueUrl']

    res = sqs.send_message(QueueUrl=test_queue_url, MessageBody='Hello Internet!')
    print(f'Message sent with ID: {res["MessageId"]}')

    messages = sqs.receive_message(QueueUrl=test_queue_url, MaxNumberOfMessages=1)
    message = messages['Messages'][0]

    print(f'Message received: {message["Body"]}')


if __name__ == '__main__':
    main()
