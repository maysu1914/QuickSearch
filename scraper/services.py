import concurrent
import math
import time
from concurrent.futures import ThreadPoolExecutor
from ssl import SSLError

import requests


class RequestService:

    def __init__(self, sleep=None):
        self.sleep = sleep
        self.executor = ThreadPoolExecutor()

    @staticmethod
    def _get_page_content(url, counter=3, dynamic_verification=False):
        """
        Content retriever
        :param sleep: time to sleep after request to prevent blocking of some sources
        :param dynamic_verification: try without SSL verify if needed
        :param url: the link whose content is to be returned
        :param counter: how many times of retrying
        :return: content of response
        """
        error_count = 0
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
        kwargs = {"timeout": 10, "headers": headers}
        for count in range(1, counter + 1):
            try:
                return requests.get(url, **kwargs).content
            except SSLError as e:
                error_count += 1
                print('Error occurred while getting page content!', count, url, e)
                if error_count >= 3:
                    raise requests.exceptions.RequestException(e)
                if dynamic_verification:
                    kwargs.update({"verify": False})
            except Exception as e:
                error_count += 1
                print('Error occurred while getting page content!', count, url, e)
                if error_count >= 3:
                    raise requests.exceptions.RequestException(e)
        return ""

    def get_page_contents(self, url_list):
        error_count = 0
        threads = []
        for index, url in enumerate(url_list):
            threads.append(self.executor.submit(self._get_page_content, url, dynamic_verification=True))
            if self.sleep:
                time.sleep(self.sleep)
        for thread in concurrent.futures.as_completed(threads):
            try:
                yield thread.result()
            except requests.exceptions.RequestException as e:
                error_count += 1
                print('Too much error occurred while getting the page contents!', e, url_list)
                if error_count >= math.ceil(len(url_list) / 3):
                    raise requests.exceptions.RequestException(e)
