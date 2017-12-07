import os


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


SYS_SETTINGS = AttrDict({
    'STORAGE_BUCKET': os.environ.get('STORAGE_BUCKET', 'difchain-digitalrecords-localdev'),
    'STORAGE_BUCKET_PREFIX': os.environ.get('STORAGE_BUCKET_PREFIX', ''),
    'QUEUE_REQUESTS': os.environ.get(
        'QUEUE_REQUESTS',
        'arn:aws:sqs:ap-southeast-2:736288480287:difchain-digitalrecords-requests-localdev'
    ),
    'QUEUE_RESULTS': os.environ.get(
        'QUEUE_RESULTS',
        'arn:aws:sqs:ap-southeast-2:736288480287:difchain-digitalrecords-results-localdev'
    ),
    'AWS_REGION': os.environ.get('AWS_REGION', 'ap-southeast-2'),
    'DOMAINS_PER_ITERATION': int(os.environ.get('DOMAINS_PER_ITERATION') or 10),
})


SCRAPY_SETTINGS = {
    'USER_AGENT': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'DEPTH_LIMIT': int(os.environ.get('DEPTH_LIMIT') or 3),
    'DEPTH_PRIORITY': 1,
    'DNS_TIMEOUT': 10,  # seconds
    'DOWNLOAD_DELAY': int(os.environ.get('DOWNLOAD_DELAY') or 10),
    'DOWNLOAD_TIMEOUT': 20,
    'DOWNLOAD_MAXSIZE': 1024 * 50,  # 50 KB at max
    'REDIRECT_MAX_TIMES': 5,
    'ROBOTSTXT_OBEY': True,
    'TELNETCONSOLE_ENABLED': False,
}
