import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import urlparse, parse_qs, urlsplit

import requests
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from urllib3.util.retry import Retry

from scraper.browsers import CustomChrome
from scraper.utils import log_time


class RequestMixin:
    def __init__(self, source, *args, **kwargs):
        if (kwargs.get('method') or 'requests') == 'requests':
            self.session = self._get_session()
        else:
            self.browser = self._get_browser()
        self.sleep = source.get('sleep_after_request', 0)
        self.thread_service = ThreadPoolExecutor()

    def _get_browser(self):
        driver = CustomChrome()
        driver.minimize_window()
        return driver

    @staticmethod
    @lru_cache
    def _get_headers():
        user_agent_values = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Safari/537.36',
            'AppleWebKit/537.36 (KHTML, like Gecko)', 'Chrome/100.0.4896.127'
        ]
        accept_values = [
            'text/html', 'application/xhtml+xml', 'application/xml;q=0.9',
            'image/avif', 'image/webp', 'image/apng', '*/*;q=0.8',
            'application/signed-exchange;v=b3;q=0.9'
        ]
        headers = {
            'user-agent': ' '.join(user_agent_values),
            'accept': ','.join(accept_values),
            'accept-language': 'en-US,en;q=0.9,tr;q=0.8,de;q=0.7'
        }
        return headers

    def _get_session(self):
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.headers = self._get_headers()
        return session

    @staticmethod
    def prepare_url(url, params):
        """
        it will prepare an url with query strings by given params
        """
        parsed_url = urlparse(url)
        parsed_params = parse_qs(parsed_url.query)
        parsed_params.update(
            {k: v[0] for k, v in parse_qs(params).items() if v}
        )
        req = PreparedRequest()
        req.prepare_url(url.split('?')[0], parsed_params)
        return req.url

    @log_time(log_args=[1])
    async def _request(self, url, **kwargs):
        method = kwargs.pop('method', 'GET')
        print(url)
        if hasattr(self, 'session'):
            try:
                return self.session.request(method, url, **kwargs)
            except requests.exceptions.SSLError as e:
                return self.session.request(method, url, verify=False, **kwargs)
        else:
            base_url = urlsplit(url)
            base_url = "{}://{}".format(base_url.scheme, base_url.netloc)
            if self.source.get('visit_homepage_first', True):
                self.browser.open(base_url)
                time.sleep(self.sleep)
            if self.source.get('refresh_browser', False):
                self.browser.quit()
                self.browser = self._get_browser()
            self.browser.open(url)
            return self.browser.page_source

    async def get_page_contents(self, url_list):
        futures = []
        for index, url in enumerate(url_list, start=1):
            if self.sleep and index > 1:
                await asyncio.sleep(self.sleep)
            futures.append(asyncio.ensure_future(self._request(url)))
        responses = asyncio.gather(*futures, return_exceptions=True)
        return await responses
