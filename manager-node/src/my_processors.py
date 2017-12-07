import datetime

from elasticsearch import Elasticsearch

from my_settings import SYS_SETTINGS
from my_logging import logger  # NOQA

es = Elasticsearch(
    hosts=[SYS_SETTINGS.ANALYTICS_ES_ENDPOINT]
)


class ResultProcessor(object):
    """
    Work with incoming results from web crawlers:
    * save them to ES
    * save them to RDS
    * return the list of further domains do crawl
    """

    def __init__(self, data):
        self.data = data
        self.process_es()
        self.process_rds()

    def prepare_data(self):
        self.data['indexed_at'] = datetime.datetime.utcnow()
        return self.data

    def process_es(self):
        tld = self.data['owner']
        if tld.endswith('.'):
            tld = tld[:-1]
        tld = tld.split('.')[-1]
        local_index_name = "{}-{}".format(SYS_SETTINGS.ANALYTICS_ES_INDEX_NAME, tld)
        # uncomment it if elastic doesn't support automatic index creation
        # es.indices.create(index=local_index_name, ignore=400)
        es.index(
            index=local_index_name,
            doc_type="recordversion",
            id=self.data['identifier'],
            body=self.prepare_data()
        )
        return

    def process_rds(self):
        return

    def get_subtasks(self):
        return self.data.get('external_domains', [])
