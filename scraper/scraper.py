import concurrent
import itertools
import math
import re
import string
import time
import urllib
from concurrent.futures.thread import ThreadPoolExecutor
from ssl import SSLError
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from requests.models import PreparedRequest
from requests.utils import requote_uri
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options as chrome_options


class CustomWebDriver(Chrome):
    def open(self, url):
        if urllib.parse.unquote(self.current_url) != url:
            self.get(url)


class Scraper:

    def __init__(self, source, max_page=5):
        self.source = source
        self.name = source.get("name")
        self.base_url = source.get("base_url")
        self.query = source.get("query")
        self.pagination_query = source.get("pagination_query")
        self.parser = self.source.get("parser")
        self.attributes = source.get("attributes")
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()
        self.driver = None

    def search(self, category, search):
        results = []
        urls = self.get_url(category, search)  # multiple results if search has list
        threads = [self.executor.submit(self.get_results, url) for url in urls]
        for thread in threads:
            results += thread.result()
        return results

    def get_url(self, category, search):
        categories = self.source.get("categories")

        if '[' in search and ']' in search:
            if category in categories:
                urls = []
                static = search
                dynamic = []

                for a, b in zip(range(1, search.count('[') + 1), range(1, search.count(']') + 1)):
                    start = self.find_nth(search, '[', a)
                    end = self.find_nth(search, ']', a) + 1
                    part = search[start:end]
                    dynamic.append(part.strip('][').split(','))
                    static = static.replace(part, '')

                for i in list(itertools.product(*dynamic)):
                    search = (' '.join(static.split()) + ' ' + ' '.join(i)).strip()
                    url = self.create_url(search, categories[category])
                    urls.append({'search': search, 'url': requote_uri(url)})
                return urls
            else:
                return []
        else:
            if category in categories:
                url = self.create_url(search, categories[category])
                # print(url)
                return [{'search': search, 'url': requote_uri(url)}]
            else:
                return []

    @staticmethod
    def get_page_content(url, counter=3, dynamic_verification=True):
        """
        Content retriever
        :param dynamic_verification: try without SSL verify if needed
        :param url: the link whose content is to be returned
        :param counter: how many times of retrying
        :return: content of response
        """
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
        verify = True
        for count in range(1, counter + 1):
            try:
                response = requests.get(url, timeout=10, headers=headers, verify=verify)
                return response.content
            except Exception as e:
                print('Error occurred while getting page content!', count, url, e)
                if dynamic_verification and type(e) == SSLError:
                    verify = False
                continue
        return ''

    @staticmethod
    def get_driver():
        extensions = ['driver/extensions/block_image_1_1_0_0.crx']
        options = chrome_options()
        # options.headless = True
        # options.add_argument("--start-maximized")
        for extension in extensions:
            options.add_extension(extension)
        driver = CustomWebDriver(executable_path="driver/chromedriver.exe", options=options)
        driver.set_window_position(-10000, 0)
        return driver

    def get_page_content_by_browser(self, url):
        if not self.driver:
            self.driver = self.get_driver()
        self.driver.open(url)
        return self.driver.page_source

    def get_contents(self, url_list):
        threads = []
        for index, url in enumerate(url_list):
            threads.append(ThreadPoolExecutor().submit(self.get_page_content, url))
            if index > 1 and index % 20 == 0:
                time.sleep(5)
            else:
                time.sleep(0.2)
        for thread in concurrent.futures.as_completed(threads):
            yield thread.result()

    @staticmethod
    def is_suitable_to_search(product_name, search):
        if product_name:
            product_name = product_name.lower()
            search = search.lower()
        else:
            return False

        search_numbers = re.findall('\d+', search)
        search_words = search.lower()

        for number in search_numbers:
            search_words = search_words.replace(number, '')

        search_words = [word if len(word) > 2 else None for word in search_words.split()]

        search_words = [i for i in search_words if i]

        for number in search_numbers:
            count = search.count(number)
            if product_name.count(number) < count:
                return False
        for word in search_words:
            count = search.count(word)
            if product_name.count(word) < count:
                return False
        return True

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

    @staticmethod
    def get_text(element):
        """
        it will parse the text of element without children's
        :param element:
        :return: string
        """
        text = ''.join(element.find_all(text=True, recursive=False)).strip()
        return text if text else element.text

    @staticmethod
    def prepare_url(url, params):
        req = PreparedRequest()
        req.prepare_url(url, params)
        return req.url

    @staticmethod
    def get_attribute_by_path(dictionary, attribute_path):
        current_attr = dictionary
        for key in attribute_path.split('.'):
            current_attr = current_attr.get(key)
            if not current_attr:
                return None
        else:
            return current_attr

    def bs_select(self, soup, dictionary, attribute_path):
        selector = self.get_attribute_by_path(dictionary, f"{attribute_path}.selector")
        return getattr(soup, selector["type"])(*selector["args"], **selector["kwargs"]) if selector else None

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []
        if soup and self.bs_select(soup, self.source, "validations.is_listing_page"):
            page_number = self.get_page_number(self.bs_select(soup, self.source, "page_number"))
            results += self.get_products(content, url['search'], "listing")
            if page_number > 1:
                page_list = [self.prepare_url(url['url'], self.pagination_query % number) for number in
                             range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'], "listing")
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, result):
        if result and isinstance(result, ResultSet):
            numbers = [max(map(int, re.findall('\d+', e.text))) for e in result if any(re.findall('\d+', e.text))]
            page = max(numbers)
            return self.max_page if page > self.max_page else page
        elif result:
            numbers = tuple(map(int, re.findall('\d+', result.text)))
            page = math.ceil(max(numbers) / self.source["page_number"]["products_per_page"]) if numbers else 1
            return self.max_page if page > self.max_page else page
        else:
            return 1

    def create_url(self, search, category):
        url = urljoin(self.base_url, self.query["path"])
        search = self.query["space"].join(search.split())
        category = category.format(search=search) if self.is_formattable(category) else category
        return url % {'category': category, 'search': search}

    def get_products(self, content, search, page_type):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in self.bs_select(soup, self.source, f"product.{page_type}"):
            data = {'source': self.name}
            for key, value in self.attributes.items():
                function = value[page_type]["function"]
                key_path = f"{key}.{page_type}"
                data[key] = getattr(self, function)(self.bs_select(product, self.attributes, key_path))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    @staticmethod
    def get_product_name(result):
        if isinstance(result, ResultSet):
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None

    def get_product_price(self, result):
        if isinstance(result, ResultSet):
            return min([int(''.join([s for s in self.get_text(e).split(',')[0] if s.isdigit()])) for e in result])
        elif result:
            return int(''.join([s for s in result.text.split(',')[0] if s.isdigit()]))
        else:
            return 0

    @staticmethod
    def get_product_info(result):
        if isinstance(result, ResultSet):
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None

    @staticmethod
    def get_product_comment_count(result):
        if isinstance(result, ResultSet):
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None
