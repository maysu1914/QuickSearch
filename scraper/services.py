import concurrent
import math
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RequestMixin:
    def __init__(self, source, *args, **kwargs):
        self.sleep = source.get("sleep_after_request", 0)
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
    @lru_cache
    def _get_session():
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _request(self, url, **kwargs):
        print(url)
        method = kwargs.pop('method', 'GET')
        kwargs.update({"headers": self._get_headers()})
        session = self._get_session()
        return session.request(method, url, **kwargs)

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
