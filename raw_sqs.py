#!/usr/bin/env python3

import boto3
import moto


@moto.mock_sqs
def main():
    sqs = boto3.client('sqs', region_name='us-west-1')
    
    test_queue_name = 'test-queue-1'
    queue = sqs.create_queue(QueueName=test_queue_name)

    #queues = sqs.list_queues(QueueNamePrefix=test_queue_name)
    #test_queue_url = queues['QueueUrls'][0]

    test_queue_url = sqs.get_queue_url(QueueName=test_queue_name)['QueueUrl']
    print(sqs.get_queue_attributes(QueueUrl=test_queue_url))

    res = sqs.send_message(QueueUrl=test_queue_url, MessageBody='Hello Internet!')
    print(f'Message sent with ID: {res["MessageId"]}')

    messages = sqs.receive_message(QueueUrl=test_queue_url, MaxNumberOfMessages=1)
    message = messages['Messages'][0]

    print(f'Message received: {message["Body"]}')


@moto.mock_sqs
def main_2():
    sqs = boto3.resource('sqs', region_name='us-west-1')
    
    test_queue_name = 'test-queue-1'
    _ = sqs.create_queue(QueueName=test_queue_name)

    #queues = sqs.list_queues(QueueNamePrefix=test_queue_name)
    #test_queue_url = queues['QueueUrls'][0]

    queue = sqs.get_queue_by_name(QueueName=test_queue_name)
    print(queue.attributes)

    res = queue.send_message(MessageBody='Hello Internet!')
    print(f'Message sent with ID: {res.get("MessageId")}')

    messages = queue.receive_messages(MaxNumberOfMessages=1)
    message = messages[0]

    print(f'Message received: {message.body}')


if __name__ == '__main__':
    main()
    #main_2()
