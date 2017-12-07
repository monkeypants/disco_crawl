#!/usr/bin/env python
import json
import time  # NOQA
import pprint  # NOQA
import sys

import boto3
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from my_logging import logger  # NOQA
from my_settings import SCRAPY_SETTINGS, SYS_SETTINGS
from my_parser import WebsiteParser


s3_client = boto3.client('s3', region_name=SYS_SETTINGS.AWS_REGION)
sqs_resource = boto3.resource('sqs', region_name=SYS_SETTINGS.AWS_REGION)


def save_s3_file(filename, body):
    # use SYS_SETTINGS to get the bucket and the prefix
    s3_client.put_object(
        ACL='private',  # 'public-read'
        Body=body,
        Bucket=SYS_SETTINGS.STORAGE_BUCKET,
        ContentEncoding='utf-8',
        ContentLength=len(body),
        # ContentMD5='string',
        # ContentType='text/html',
        Key=filename,
        # Metadata={
        #     'string': 'string'
        # },
        # StorageClass='STANDARD'|'REDUCED_REDUNDANCY'|'STANDARD_IA',
    )


class GenericWebsiteSpider(CrawlSpider):
    name = 'myspider'
    start_urls = []  # 'http://ausdigital.org'
    allowed_domains = []  # "ausdigital.org"

    rules = (
        Rule(LinkExtractor(allow=('', )), callback='parse_item'),
    )

    def __init__(self, *args, **kwargs):
        domain = kwargs.pop('domain')
        self.start_urls = ['http://{}'.format(domain)]
        self.allowed_domains = [domain]
        super().__init__(*args, **kwargs)

    def parse_item(self, response):
        item = scrapy.Item()
        try:
            parser = WebsiteParser(
                response,
                allowed_domains=self.allowed_domains
            )

            # save response.body to S3
            save_s3_file(
                parser.get_s3_filename(),
                parser.get_body()
            )

            # send SQS message about S3 saved object with the list of external links
            if MODE == 'sqs':
                results_queue.send_message(
                    MessageBody=json.dumps(parser.get_result())
                )
            else:
                # for demo run just print it
                pprint.pprint(parser.get_result())
        except Exception as e:
            logger.exception(e)
        return item


requests_queue = sqs_resource.get_queue_by_name(
    QueueName=SYS_SETTINGS.QUEUE_REQUESTS.split(':')[-1],
    QueueOwnerAWSAccountId=SYS_SETTINGS.QUEUE_REQUESTS.split(':')[-2]
)
results_queue = sqs_resource.get_queue_by_name(
    QueueName=SYS_SETTINGS.QUEUE_RESULTS.split(':')[-1],
    QueueOwnerAWSAccountId=SYS_SETTINGS.QUEUE_RESULTS.split(':')[-2]
)


if __name__ == '__main__':
    MODE = None
    if len(sys.argv) == 2:
        MODE = 'domain'
        logger.info("Fetching domain by name...")
        domain_name = sys.argv[1]
        process = CrawlerProcess(SCRAPY_SETTINGS)
        process.crawl(GenericWebsiteSpider, domain=domain_name)
        process.start()  # the script will block here until the crawling is finished
        logger.info("Domain %s fetch finished", domain_name)
    else:
        MODE = 'sqs'

        while True:
            # standard working cycle
            logger.info("Standard cycle started...")
            domains_to_process = []

            # get up to 5 messages from the queue
            for msg in requests_queue.receive_messages(
                MaxNumberOfMessages=SYS_SETTINGS.DOMAINS_PER_ITERATION, WaitTimeSeconds=5
            ):
                domain_name = msg.body
                logger.info("Going to crawl %s", domain_name)
                domains_to_process.append(domain_name)
                msg.delete()

            if domains_to_process:
                # any work exists
                process = CrawlerProcess(SCRAPY_SETTINGS)
                for domain in domains_to_process:
                    process.crawl(GenericWebsiteSpider, domain=domain_name)
                process.start()  # the script will block here until the crawling is finished
                logger.info("Standard cycle finished, going to run another")
                exit(0)  # if we don't kill process we waste some memory and have Reactor exception
                # another solution is https://doc.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process  # NOQA
            else:
                logger.info("No messages to process, sleeping...")
            time.sleep(10)
