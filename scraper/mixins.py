import concurrent
import math
import string
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import urlparse, parse_qs

import requests
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from urllib3.util.retry import Retry


class RequestMixin:
    def __init__(self, source, *args, **kwargs):
        self.session = self._get_session()
        self.sleep = source.get('sleep_after_request', 0)
        self.thread_service = ThreadPoolExecutor()

    @staticmethod
    @lru_cache
    def _get_headers():
        headers = {
            'user-agent': ' '.join(['Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                                    'AppleWebKit/537.36 (KHTML, like Gecko)',
                                    'Chrome/100.0.4896.127', 'Safari/537.36']),
            'accept': ','.join(
                ['text/html', 'application/xhtml+xml', 'application/xml;q=0.9', 'image/avif', 'image/webp',
                 'image/apng', '*/*;q=0.8', 'application/signed-exchange;v=b3;q=0.9']),
            'accept-language': 'en-US,en;q=0.9,tr;q=0.8,de;q=0.7'
        }
        return headers

    @staticmethod
    def _get_session():
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    @staticmethod
    def prepare_url(url, params):
        """
        it will prepare an url with query strings by given params
        """
        parsed_url = urlparse(url)
        parsed_params = parse_qs(parsed_url.query)
        parsed_params.update({k: v[0] for k, v in parse_qs(params).items() if v})
        req = PreparedRequest()
        req.prepare_url(url.split('?')[0], parsed_params)
        return req.url

    def _request(self, url, **kwargs):
        print(url)
        method = kwargs.pop('method', 'GET')
        kwargs.update({'headers': self._get_headers()})
        return self.session.request(method, url, **kwargs)

    def get_page_contents(self, url_list):
        error_count = 0
        threads = []
        for url in url_list:
            threads.append(self.thread_service.submit(self._request, url))
            time.sleep(self.sleep)
        for thread in concurrent.futures.as_completed(threads):
            try:
                yield thread.result().content
            except requests.exceptions.RequestException as e:
                error_count += 1
                print('Too much error occurred while getting the page contents!', e, url_list)
                if error_count >= math.ceil(len(url_list) / 3):
                    raise


class ToolsMixin:

    @staticmethod
    def is_formattable(text):
        return any([tup[1] for tup in string.Formatter().parse(text) if tup[1] is not None])

    @staticmethod
    def find_nth(haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start + len(needle))
            n -= 1
        return start
