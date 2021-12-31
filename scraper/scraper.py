import itertools
import math
import re
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from requests.utils import requote_uri

from scraper.services import RequestService
from scraper.utils import get_text, is_formattable, get_attribute_by_path, prepare_url, find_nth


class Scraper:
    threads = []

    def __init__(self, source, max_page=5):
        self.source = source
        self.name = source.get("name")
        self.base_url = source.get("base_url")
        self.query = source.get("query")
        self.pagination_query = source.get("pagination_query")
        self.parser = self.source.get("parser")
        self.attributes = source.get("attributes")
        self.first_next = get_attribute_by_path(source, "page_number.first_next", default=2)
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()
        self.request_service = RequestService(sleep=source.get("sleep_after_request"))
        self.driver = None

    def search(self, category, search):
        error_count = 0
        results = []
        urls = self.get_urls(category, search)  # multiple results if search has list
        # threads = [self.executor.submit(self.get_results, url) for url in urls]
        # for thread in threads:
        #     results += thread.result()
        for url in urls:
            try:
                results += self.get_results(url)
            except requests.exceptions.RequestException as e:
                error_count += 1
                if error_count >= math.ceil(len(urls) / 4):
                    print(f"Too much error occurred in {self.name}", e)
                    break
        return results

    def get_urls(self, category, search):
        categories = self.source.get("categories")
        urls = []

        if category in categories:
            for search_text in self.get_all_combinations(search):
                url = self.create_url(search_text, categories[category])
                urls.append({'search': search_text, 'url': requote_uri(url)})
        return urls

    @staticmethod
    def get_all_combinations(search):
        searches = []
        if '[' in search and ']' in search:
            static = search
            dynamic = []

            for a, b in zip(range(1, search.count('[') + 1), range(1, search.count(']') + 1)):
                start = find_nth(search, '[', a)
                end = find_nth(search, ']', a) + 1
                part = search[start:end]
                dynamic.append(part.strip('][').split(','))
                static = static.replace(part, '')
            for i in list(itertools.product(*dynamic)):
                searches.append((' '.join(static.split()) + ' ' + ' '.join(i)).strip())
        else:
            searches.append(search)

        return searches

    def check_the_suitability(self, product_name, searches):
        if not isinstance(searches, list):
            searches = [searches]
        return any((self.is_suitable_to_search(product_name, search) for search in searches))

    @staticmethod
    def is_suitable_to_search(product_name, search):
        acceptable_length = 3
        if product_name and len(search) >= acceptable_length:
            product_name = product_name.lower()
            search = search.lower()
        else:
            return False

        search_numbers = re.findall('\d+', search)
        search_words = search.lower()

        for number in search_numbers:
            search_words = search_words.replace(number, '')

        search_words = [word for word in search_words.split() if len(word) >= acceptable_length]

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
    def bs_select(soup, dictionary, attribute_path):
        selector = get_attribute_by_path(dictionary, f"{attribute_path}.selector")
        return getattr(soup, selector["type"])(*selector["args"], **selector["kwargs"]) if selector else None

    def get_results(self, url):
        content = next(self.request_service.get_page_contents([url.get('url')]))
        soup = BeautifulSoup(content, "lxml")
        results = []
        if soup and self.bs_select(soup, self.source, "validations.is_listing_page"):
            page_number = self.get_page_number(self.bs_select(soup, self.source, "page_number"))
            results += self.get_products(content, url['search'], "listing")
            if page_number > 1:
                page_list = [prepare_url(url['url'], self.pagination_query % number) for number in
                             range(self.first_next, page_number + 1)]
                contents = self.request_service.get_page_contents(page_list)
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
            numbers = tuple(map(int, re.findall('\d+', result.text.replace(',', '').replace('.', ''))))
            page = math.ceil(max(numbers) / self.source["page_number"]["products_per_page"]) if numbers else 1
            return self.max_page if page > self.max_page else page
        else:
            return 1

    def create_url(self, search, category):
        url = urljoin(self.base_url, self.query["path"])
        search = self.query["space"].join(search.split())
        category = category.format(search=search) if is_formattable(category) else category
        return url % {'category': category, 'search': search}

    def get_products(self, content, search, page_type):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in self.bs_select(soup, self.source, f"product.{page_type}"):
            acceptable = True
            data = {'source': self.name}
            for key, value in self.attributes.items():
                function = value[page_type]["function"]
                key_path = f"{key}.{page_type}"
                data[key] = getattr(self, function)(self.bs_select(product, self.attributes, key_path))
                if value.get("required") and not data[key]:
                    acceptable = False
            data['suitable_to_search'] = self.check_the_suitability(data['name'], search)
            if acceptable:
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

    @staticmethod
    def get_product_price(result):
        if isinstance(result, ResultSet):
            numbers = [''.join([s for s in get_text(e).split(',')[0] if s.isdigit()]) for e in result]
            return min([int(number) for number in numbers]) if numbers and all(numbers) else 0
        elif result:
            number = ''.join([s for s in result.text.split(',')[0] if s.isdigit()])
            return int(number) if number else 0
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

    @staticmethod
    def get_discount_calculated(result):
        if isinstance(result, ResultSet):
            numbers = [''.join([s for s in get_text(e).split(',')[0] if s.isdigit()]) for e in result]
            values = [int(number) for number in numbers] if numbers and all(numbers) else [0]
            min_val = min(values)
            max_val = max(values)
            return int((max_val - min_val) / max_val * 100) if min_val != max_val else 0
        else:
            return 0
