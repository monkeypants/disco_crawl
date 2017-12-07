import datetime  # NOQA
import base58
import random
from urllib.parse import urlparse

import dateutil.parser
import multihash
# from goose import Goose
from bs4 import BeautifulSoup

from randomname import get_random_name


class WebsiteParser(object):
    """
    Receive response from scrapy
    Return the list of items to save:
     * HTML content to save to S3
     * parsed dict with information to send to SQS
    """

    def __init__(self, url, body, external_links, internal_links, resp):
        self.url = url
        self.body = body
        self.internal_links = internal_links
        self.external_links = external_links
        self.resp = resp

    def get_body(self):
        return self.body

    def get_content_multihash(self):
        return base58.b58encode(
            bytes(multihash.encode(self.get_body(), multihash.SHA1))
        )

    def get_s3_filename(self):
        return self.get_content_multihash()

    def get_result(self):
        """
        Return parse results
        https://github.com/difchain/rmaas/blob/master/docs/WebCrawler_Client.md
        """
        soup = BeautifulSoup(self.get_body(), "lxml")
        [x.extract() for x in soup.findAll('script')]
        [x.extract() for x in soup.findAll('ul')]
        [x.extract() for x in soup.findAll('table')]
        [x.extract() for x in soup.findAll('form')]

        owner = urlparse(self.url).netloc
        identifier = self.url
        result = {
            # RecordName area
            'identifier': identifier,
            'owner': owner,
            # RecordVersion area
            'Hash': self.get_content_multihash(),
            'RecordsAuthority': 'naa.gov.au:gda{}'.format(random.randint(15, 30)),
            'Title': soup.title.text.replace('\n', '').strip(),
            'Description': self._get_description(soup),
            'Author': get_random_name(),
            'DateCreated': self._get_date_created(),
            'Classification': 'UNCLASSIFIED',
            'Language': self._get_language(),
            # object
            'size': len(self.get_body()),
            'MIMEType': self._get_mimetype(),
            # etc
            's3_filename': self.get_s3_filename(),
            'external_domains': self.external_links,
            'links': self.internal_links,
            'keywords': self.get_keywords(soup)
        }
        return result

    def _get_description(self, soup):
        all_paragraphs = [s.extract().text for s in soup('p')]
        ret = ''
        for t in all_paragraphs:
            l = len(t)
            if l > 150 and 'script' not in t.lower():
                return t
            if l > len(ret):
                ret = t
        if not ret:
            ret = soup.get_text(strip=True)
        return ret[:300].strip()

    def _get_mimetype(self):
        result = self.resp.get('content-type')
        return result or 'text/html'

    def _get_date_created(self):
        lm = self.resp.get('last-modified')
        if lm:
            lm = dateutil.parser.parse(lm)
            if lm:
                lm = lm.isoformat()
        return lm

    def get_keywords(self, soup):
        kws = set()
        for tag in ['h1', 'h2', 'h3', 'h4']:
            for header in soup.find_all(tag):
                words = [w for w in header.text.split() if len(w) > 6]
                for w in words:
                    kws.add(w)
        return list(kws)

    def _get_language(self):
        return 'en-us'
