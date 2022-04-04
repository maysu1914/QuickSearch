import concurrent
import math
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from ssl import SSLError

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RequestService:

    def __init__(self, sleep=0):
        self.sleep = sleep
        self.executor = ThreadPoolExecutor()

    @staticmethod
    @lru_cache
    def _get_headers():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)',
            "Accept": "text/html,application/xhtml+xml,application/xml,application/signed-exchange"
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
        kwargs.update({"headers": self._get_headers()})
        session = self._get_session()
        return session.get(url, **kwargs)

    def _get_page_content(self, url, **kwargs):
        """
        Content retriever
        :param url: the link whose content is to be returned
        :return: content of response
        """
        print(url)
        try:
            return self._request(url, **kwargs).content
        except requests.exceptions.RequestException as e:
            print('Error occurred while getting page content!', url, e)
            raise

    def get_page_contents(self, url_list):
        error_count = 0
        threads = []
        for url in url_list:
            threads.append(self.executor.submit(self._get_page_content, url))
            time.sleep(self.sleep)
        for thread in concurrent.futures.as_completed(threads):
            try:
                yield thread.result()
            except requests.exceptions.RequestException as e:
                error_count += 1
                print('Too much error occurred while getting the page contents!', e, url_list)
                if error_count >= math.ceil(len(url_list) / 3):
                    raise
