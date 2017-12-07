#!/usr/bin/env python
import datetime
import json
import time  # NOQA
import pprint  # NOQA
import sys

import boto3
import redis

from my_logging import logger  # NOQA
from my_settings import SYS_SETTINGS
from my_processors import ResultProcessor

s3_client = boto3.client('s3', region_name=SYS_SETTINGS.AWS_REGION)
sqs_resource = boto3.resource('sqs', region_name=SYS_SETTINGS.AWS_REGION)

requests_queue = sqs_resource.get_queue_by_name(
    QueueName=SYS_SETTINGS.QUEUE_REQUESTS.split(':')[-1],
    QueueOwnerAWSAccountId=SYS_SETTINGS.QUEUE_REQUESTS.split(':')[-2]
)
results_queue = sqs_resource.get_queue_by_name(
    QueueName=SYS_SETTINGS.QUEUE_RESULTS.split(':')[-1],
    QueueOwnerAWSAccountId=SYS_SETTINGS.QUEUE_RESULTS.split(':')[-2]
)

redis_db = redis.StrictRedis.from_url(
    SYS_SETTINGS.REDIS_CONNECTION
)


def process_result(data):
    pr = ResultProcessor(data)
    # if we have some external domains - crawl them here
    subtasks = pr.get_subtasks()
    for subtask in subtasks:
        subtask_already_sent = bool(redis_db.get(subtask))
        if not subtask_already_sent:
            # TODO: deduplicate using Redis or Postgres, not global variable
            redis_db.set(subtask, datetime.datetime.utcnow().isoformat())
            logger.info("Sending subtask %s...", subtask)
            requests_queue.send_message(
                MessageBody=subtask
            )
    return


if len(sys.argv) == 2:
    # ./worker.py jsonfile.json usage
    demo_data = json.loads(open(sys.argv[1]).read())
    process_result(demo_data)
else:
    # daemon usage
    while True:
        # get up to 5 messages from the queue
        for msg in results_queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=5):
            try:
                data = json.loads(msg.body)
            except Exception as e:
                logger.error("Wrong message received and dropped: %s", msg.body)
            else:
                msg.delete()
                process_result(data)
