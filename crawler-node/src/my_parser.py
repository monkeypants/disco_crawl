# import hashlib
import base58
from urllib.parse import urlparse

import dateutil.parser
import multihash
from goose import Goose
# from lxml import etree
from scrapy.linkextractors import LinkExtractor


class WebsiteParser(object):
    """
    Receive response from scrapy
    Return the list of items to save:
     * HTML content to save to S3
     * parsed dict with information to send to SQS
    """

    def __init__(self, response, allowed_domains=[]):
        self.response = response
        self.allowed_domains = allowed_domains
        self.my_le = LinkExtractor(allow=('', ))

    def get_body(self):
        return self.response.body

    def get_content_multihash(self):
        return base58.b58encode(
            bytes(multihash.encode(self.response.body, multihash.SHA1))
        )

    def get_s3_filename(self):
        # return hashlib.sha256(self.response.url.encode('utf-8')).hexdigest()
        return self.get_content_multihash()

    def get_result(self):
        """
        Return parse results
        https://github.com/difchain/rmaas/blob/master/docs/WebCrawler_Client.md
        """
        gs = Goose()
        parsed_article = gs.extract(raw_html=self.get_body())

        owner = urlparse(self.response.url).netloc
        identifier = self.response.url  # .replace('https://', '').replace('http://', '')
        result = {
            # RecordName area
            'identifier': identifier,
            'owner': owner,
            # RecordVersion area
            'Hash': self.get_content_multihash(),
            'RecordsAuthority': 'naa.gov.au:gda21',
            'Title': parsed_article.title,
            'Description': parsed_article.cleaned_text[:300],
            'Author': self._get_version_author(),
            'DateCreated': self._get_date_created(),
            'Classification': 'UNCLASSIFIED',
            'Language': self._get_language(),
            # object
            'size': len(self.response.body),
            'MIMEType': self._get_mimetype(),
            # etc
            's3_filename': self.get_s3_filename(),
            'external_domains': self._get_external_domains(),
            'links': self._get_links(),
        }
        return result

    # def _get_version_title(self):
    #     return self.response.selector.xpath('//title/text()').extract_first() or '?'

    # def _get_version_description(self):
    #     tree = etree.HTML(self.response.body)
    #     etree.strip_tags(tree)
    #     text_spaced = etree.tounicode(tree, method='text').replace('\n', ' ').strip()
    #     text = ' '.join(x for x in text_spaced.split() if x)
    #     return text[:300] if text else '?'

    def _get_version_author(self):
        return 'John the Dropbear'

    def _get_mimetype(self):
        result = self.response.headers.get('Content-Type')
        if result:
            result = result.decode('utf-8')
        return result or 'text/html'

    def _get_date_created(self):
        lm = self.response.headers.get('Last-Modified')
        if lm:
            lm = dateutil.parser.parse(lm)
            if lm:
                lm = lm.isoformat()
        return lm

    def _get_language(self):
        return 'en-us'

    def _get_external_domains(self):
        # get the list of external domain names linked from this page
        external_domains = set()
        for link in self.my_le.extract_links(self.response):
            parsed_link = urlparse(link.url)
            if parsed_link.netloc not in self.allowed_domains:
                external_domains.add(parsed_link.netloc)
        return sorted(list(external_domains))

    def _get_links(self):
        links = set()
        for link in self.my_le.extract_links(self.response):
            links.add(link.url)
        return sorted(list(links))
