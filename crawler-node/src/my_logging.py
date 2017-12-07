import logging
from logging.config import dictConfig

logging_config = {
    'version': 1,
    'formatters': {
        'f': {
            'format': '%(levelname)s [%(asctime)s] %(name)s %(message)s'
        }
    },
    'handlers': {
        'h': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.DEBUG
        }
    },
    'loggers': {
        '': {
            'handlers': ['h'],
            'level': logging.INFO,
        },
        'root': {
            'handlers': ['h'],
            'level': logging.INFO,
        },
        'botocore': {
            'handlers': ['h'],
            'level': logging.WARNING,
            'propagate': False,
        },
        'boto3': {
            'handlers': ['h'],
            'level': logging.WARNING,
            'propagate': False,
        },
        'boto': {
            'handlers': ['h'],
            'level': logging.WARNING,
            'propagate': False,
        },
        'nose': {
            'handlers': ['h'],
            'level': logging.WARNING,
            'propagate': False,
        },
        'scrapy': {
            'handlers': ['h'],
            'level': logging.INFO,
            'propagate': False
        },
    }
}

dictConfig(logging_config)

logger = logging.getLogger('crawler_node')
