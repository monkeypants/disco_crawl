#!/usr/bin/env python
import json
import pprint
import traceback
import random
import sys
import signal
import logging
import httplib2
from contextlib import contextmanager
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import gevent
from gevent import monkey, queue, event, pool, sleep
monkey.patch_all()  # NOQA

import boto3
from bs4 import BeautifulSoup
from my_settings import SYS_SETTINGS
from my_parser import WebsiteParser


MAX_ERRORS_NUMBER = 10
extensions_blacklist = ('.gif', '.jpeg', '.png', '.docx', '.zip', '.tar', '.svg', '.exe')


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


logger = logging.getLogger(__name__)
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


def save_s3_file(filename, body):
    # use SYS_SETTINGS to get the bucket and the prefix
    s3_client.put_object(
        ACL='private',  # 'public-read'
        Body=body,
        Bucket=SYS_SETTINGS.STORAGE_BUCKET,
        ContentEncoding='utf-8',
        ContentLength=len(body),
        Key=filename,
    )


def ua(): return "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0"


class Job(object):
    """Encapsulation of a job to put in the job queue.  Contains at least
    a URL, but can also have custom headers or entirely custom meta
    information.  The response object and data are tacked onto this object,
    which is then returned to the scraper for processing."""
    default_headers = {
        'Accept': 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;',
        'Accept-Encoding': 'gzip,deflate',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self, url, headers=None, meta=None, method='GET'):
        self.__url = url
        self.method = method
        self.headers = dict(self.default_headers)
        self.headers.update(headers or {})
        self.headers['User-Agent'] = ua()
        self.meta = meta

    def __hash__(self):
        return hash(self.url)

    def __cmp__(self, other):
        return hash(self) - hash(other)

    def __repr__(self):
        return '<Job: %s (%s)>' % (
            self.url,
            'done: %d' % len(self.data) if hasattr(self, 'data') else 'pending',
        )

    url = property(lambda self: self.__url)


class Crawler(object):
    """Simple crawler based on gcrawler, but with a rolling inq that can be
    added to.  The crawler is done when the workers have no more jobs and
    there are no more urls in the queue."""
    seen_jobs = set()

    def __init__(self, spider, timeout=2, worker_count=4, pipeline_size=100):
        self.spider = spider
        self.spider.crawler = self
        self.timeout = timeout
        self.count = worker_count
        self.inq = queue.Queue(0)
        self.outq = queue.Queue(pipeline_size)
        self.jobq = queue.Queue()
        self.pool = pool.Pool(worker_count)
        self.worker_finished = event.Event()

        for job in getattr(self.spider, 'jobs', []):
            self.add_job(job)

    def start(self):
        """Start the crawler.  Starts the scheduler and pipeline first, then
        adds jobs to the pool and waits for the scheduler and pipeline to
        finish.  The scheduler itself shuts down the pool and waits on that,
        so it's not required to watch the pool."""
        # add the spider's jobs first
        for url in self.spider.urls:
            self.add_job(url)
        # start the scheduler & the pipeline
        self.scheduler_greenlet = gevent.spawn(self.scheduler)
        self.pipeline_greenlet = gevent.spawn(self.pipeline)
        self.scheduler_greenlet.join()

    def add_job(self, job, **kwargs):
        """Add a job to the queue.  The job argument can either be a Job object
        or a url with keyword arguments to be passed to the Job constructor."""
        if isinstance(job, str):
            job = Job(job, **kwargs)
        # do not visit previously viewed urls
        if job in self.seen_jobs:
            return
        self.jobq.put(job)

    def scheduler(self):
        """A simple job scheduler.  Presuming it's started after there is at
        least one job, it feeds jobs to the job queue to a synchronous worker
        job queue one at a time.  When the worker queue fills up, the
        scheduler will block on the put() operation.  When job queue is empty,
        the scheduler will wait for the workers to finish.  If the job queue
        is empty and no workers are active, the pool's stopped."""
        logger = logging.getLogger(__name__ + '.scheduler')
        while True:
            # join dead greenlets
            for greenlet in list(self.pool):
                if greenlet.dead:
                    self.pool.discard(greenlet)
            try:
                logger.debug("Fetching job from job queue.")
                job = self.jobq.get_nowait()
            except queue.Empty:
                logger.debug("No jobs remaining.")
                if self.pool.free_count() != self.pool.size:
                    logger.debug("%d workers remaining, waiting..." % (self.pool.size - self.pool.free_count()))
                    self.worker_finished.wait()
                    self.worker_finished.clear()
                    continue
                else:
                    logger.debug("No workers left, shutting down.")
                    return self.shutdown()
            self.pool.spawn(self.worker, job)

    def shutdown(self):
        """Shutdown the crawler after the pool has finished."""
        self.pool.join()
        self.outq.put(StopIteration)
        self.pipeline_greenlet.join()
        return True

    def worker(self, job, logger=logging.getLogger(__name__ + '.worker')):
        """A simple worker that fetches urls based on jobs and puts the
        ammended jobs on the outq for processing in the pipeline thread.
        After each job is fetched, but before the worker sets the finished
        event, the spider's preprocess method will be called on the job. This
        is its opportunity to add urls to the job queue.  Heavy processing
        should be done via the pipeline in postprocess."""
        logger.debug("starting: %r" % job)
        # you need to create a new Http instance per greenlet, see ticket:
        #   http://code.google.com/p/httplib2/issues/detail?id=5
        h = httplib2.Http()
        try:
            sleep(self.spider.sleep_seconds + random.randint(1, 3))
            job.response, job.data = h.request(job.url, method=job.method, headers=job.headers)
            self.spider.preprocess(job)
        except Exception as e:
            formatted = traceback.format_exc()
            if 'ssl.CertificateError' in formatted or 'socket.gaierror' in formatted or 'httplib2.' in formatted:
                self.spider.errors += 1
            logger.error("Preprocessing error:\n%s" % formatted)
        else:
            self.outq.put(job)
            self.worker_finished.set()
            # logger.debug("finished: %r" % job)
        raise gevent.GreenletExit('success')

    def pipeline(self):
        """A post-processing pipeline greenlet which keeps post-processing from
        interfering with network wait parallelization of the worker pool."""
        logger = logging.getLogger(__name__ + '.pipeline')
        for job in self.outq:
            try:
                self.spider.postprocess(job)
            except:
                logger.error("error:\n%s" % traceback.format_exc())
        logger.debug("finished processing.")


def run(spider, **kwargs):
    Crawler(spider, **kwargs).start()


class MySpider(object):
    def __init__(self, domain_name):
        self.domain_name = domain_name
        self.pure_domain = domain_name[len('www.'):] if domain_name.startswith('www.') else domain_name
        self.www_domain = 'www.' + domain_name if not domain_name.startswith('www.') else domain_name
        if self.pure_domain.endswith('/'):
            self.pure_domain = self.pure_domain[:-1]
        if self.www_domain.endswith('/'):
            self.www_domain = self.www_domain[:-1]
        self.first_url = "http://" + domain_name
        self.urls = set()
        self.urls.add(self.first_url)
        self.results = []
        self.errors = 0

        # fetch robots.txt file and parse it
        self.robots = None
        self.sleep_seconds = 2

        try:
            with time_limit(10):
                self.robots = RobotFileParser(
                    'http://' + self.domain_name + '/robots.txt'
                )
                self.robots.read()
        except TimeoutException:
            logger.error("Timeout fetching the robots.txt file, ignoring the website")
            exit(10)
        except Exception as e:
            # logger.exception(e)
            logger.error("Corrupted robots.txt file")
        else:
            try:
                if self.robots:
                    self.rrate = self.robots.request_rate("*")
                    if self.rrate:
                        self.sleep_seconds = max(self.rrate.seconds or 1, 1)
            except Exception as e:
                pass

        if self.sleep_seconds > 30:
            logger.error("too slow website (expects timeout %s), ignoring", self.sleep_seconds)

    def is_domain_local(self, domain):
        if not domain:
            return True
        if domain in (self.pure_domain, self.www_domain):
            return True
        return False

    def preprocess(self, job):
        # print("Preprocess")
        # print(job)
        pass

    def postprocess(self, job):
        extra_domains = set()
        internal_links = set()

        if not hasattr(job, 'data') or not job.data:
            return

        content_type = job.response.get('content-type', 'binary/octet-stream')
        if not content_type.startswith('text/'):
            print("Ignore non-text url {}".format(job.url))
            return

        if len(job.data) > 1024 * 100:
            # print("Too big response url {}".format(job.url))
            return

        print("Processing {}".format(job.url))

        soup = BeautifulSoup(job.data.decode('utf-8'), "lxml")
        for link in soup.find_all('a'):
            link = link.get('href')
            if not link:
                continue
            if link.startswith('mailto') or link.startswith('tel:'):
                continue
            if link.startswith('#') or link.startswith('javascript:'):
                continue
            parsed_url = urlparse(link)
            if self.is_domain_local(parsed_url.netloc):
                # local link
                noslash_link = link[:-1] if link.endswith('/') else link
                if link not in self.urls and noslash_link not in self.urls:
                    internal_links.add(link)
                    self.urls.add(link)
                    self.crawl_sublink(link)
                # else - ignore duplicate
            else:
                # external link
                extra_domains.add(parsed_url.netloc)
        parser = WebsiteParser(
            url=job.url,
            body=job.data,
            external_links=list(extra_domains),
            internal_links=list(internal_links),
            resp=job.response
        )

        # save response.body to S3
        save_s3_file(
            parser.get_s3_filename(),
            parser.get_body()
        )

        self.results.append(parser.get_result())

    def crawl_sublink(self, url):
        for blacklisted in extensions_blacklist:
            if url.endswith(blacklisted):
                return
        if self.pure_domain.endswith('.gov.au'):
            if len(self.urls) > 3000:
                return
        else:
            # non-gov-au website
            if len(self.urls) > 500:
                return

        if self.robots and not self.robots.can_fetch("*", url):
            return

        if self.errors > MAX_ERRORS_NUMBER:
            logger.error("Reached %s errors for %s", self.errors, self.pure_domain)
            return
        if url.startswith('//'):
            url = 'http:' + url
        if not url.startswith('http://') and not url.startswith('https://'):
            if not url.startswith('/'):
                url = '/' + url
            new_url = self.first_url + url
            url = new_url
        self.crawler.add_job(url)


if __name__ == "__main__":
    MODE = None
    if len(sys.argv) == 2:
        MODE = 'domain'
        logger.info("Fetching domain by name...")
        domain_name = sys.argv[1]
        spider = MySpider(domain_name)
        run(spider)
        pprint.pprint(spider.results)
        logger.info("Domain %s fetch finished", domain_name)
    else:
        MODE = 'sqs'

        before_restart = 3

        while before_restart > 0:
            # standard working cycle
            # get up to 5 messages from the queue
            for msg in requests_queue.receive_messages(
                MaxNumberOfMessages=1, WaitTimeSeconds=5
            ):
                msg.delete()
                domain_name = msg.body
                print("Going to crawl {}".format(domain_name))
                spider = MySpider(domain_name)
                run(spider)
                before_restart -= 1

                # send SQS message about S3 saved object with the list of external links
                # send them in bulk
                if spider.results:
                    rendered_results = json.dumps(spider.results)
                    if len(rendered_results) < 1:  # 1024 * 256
                        results_queue.send_message(
                            MessageBody=rendered_results
                        )
                    else:
                        for chunk in zip(*[iter(spider.results)]*128):
                            # split to 2 parts, which will be fine in 99% cases
                            try:
                                results_queue.send_message(
                                    MessageBody=json.dumps(list(chunk))
                                )
                            except Exception as e:
                                logger.exception(e)
                print("Done: {}, {} pages".format(domain_name, len(spider.results)))
