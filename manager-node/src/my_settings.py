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

    'REDIS_CONNECTION': os.environ.get(
        'REDIS_CONNECTION',
        # 'rediss://[:password]@localhost:6379/0'
        'redis://localhost:6379/0'
    ),

    'ANALYTICS_ES_ENDPOINT': os.environ.get('ANALYTICS_ES_ENDPOINT', 'localhost:9201'),
    'ANALYTICS_ES_INDEX_NAME': os.environ.get('ANALYTICS_ES_INDEX_NAME', 'versions'),

    # 'PG_HOST': os.environ.get('PG_HOST', 'localhost'),
    # 'PG_PORT': os.environ.get('PG_HOST', '5432'),
    # 'PG_DB': os.environ.get('PG_DB', 'digitalrecords'),
    # 'PG_USER': os.environ.get('PG_USER', 'digitalrecords'),
    # 'PG_PASSWORD': os.environ.get('PG_PASSWORD', 'digitalrecords'),
})
