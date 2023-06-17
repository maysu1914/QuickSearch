import asyncio
import hashlib
import itertools
import json
import logging
import math
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import ResultSet
from price_parser import Price
from requests.utils import requote_uri

from scraper.mixins import RequestMixin
from scraper.utils import (
    get_attribute_by_path, log_time, is_formattable, find_nth
)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Scraper(RequestMixin):
    default_first_page = 1
    minimum_search_word_length = 3

    def __init__(self, source, *args, **kwargs):
        super(Scraper, self).__init__(source, *args, **kwargs)
        self.source = source
        self.max_page = kwargs.get('max_page', 3)

    @property
    def name(self):
        return self.source.get('name')

    @property
    def base_url(self):
        return self.source.get('base_url')

    @property
    def query(self):
        return self.source.get('query')

    @property
    def pagination_query(self):
        return self.source.get('pagination_query')

    @property
    def parser(self):
        return self.source.get('parser')

    @property
    def attributes(self):
        return self.source.get('attributes')

    @property
    def first_page(self):
        return get_attribute_by_path(
            self.source, 'page_number.first_page', self.default_first_page
        )

    @property
    def products_per_page(self):
        return self.source['page_number']['products_per_page']

    @property
    def pagination_method(self):
        method = self.source['page_number']['method']
        return getattr(self, 'get_page_from_{}'.format(method))

    def get_page_from_total(self, value):
        return math.ceil(max(value) / self.products_per_page)

    def get_page_from_pagination(self, value):
        return max(value)

    @staticmethod
    def _get_all_combinations(search):
        if any(char not in search for char in ['[', ']']):
            return [search]

        searches = []
        static = search
        dynamic = []
        openings = search.count('[')
        closings = search.count(']')
        for a, b in zip(range(1, openings + 1), range(1, closings + 1)):
            start = find_nth(search, '[', a)
            end = find_nth(search, ']', a) + 1
            part = search[start:end]
            dynamic.append(part.strip('][').split(','))
            static = static.replace(part, '%s')
        for i in list(itertools.product(*dynamic)):
            searches.append((' '.join(static.split()) % i).strip())

        return searches

    def create_url(self, search, category):
        url = urljoin(self.base_url, self.query['path'])
        space_char = self.query.get('space')
        search = space_char and space_char.join(search.split()) or search
        category = category.format(search=search) if is_formattable(
            category) else category
        return url % {'category': category, 'search': search}

    def get_urls(self, category, search):
        categories = self.source.get('categories')
        urls = []

        if category in categories:
            for search_text in self._get_all_combinations(search):
                url = self.create_url(search_text, categories[category])
                urls.append({'search': search_text, 'url': requote_uri(url)})
        return urls

    def generate_paginated_urls(self, url, start_page, end_page):
        urls = []
        for number in range(start_page, end_page + 1):
            urls.append(self.prepare_url(url, self.pagination_query % number))
        return urls

    def is_suitable_to_search(self, product_name, search):
        normalizer = re.compile(r'[^A-Za-z0-9]+')
        product_name = normalizer.sub('', product_name).lower()
        search = search.lower()

        # find all numbers
        numbers = re.findall(r'\d+', search)

        # remove numbers, they won't be included minimum word length limit
        _search = search
        for number in numbers:
            _search = _search.replace(number, '', 1)

        # minimum word length limit will be applied only to texts
        _search = [
            word for word in _search.split()
            if len(word) >= self.minimum_search_word_length
        ]

        if not (_search or numbers):
            return False

        # not suitable if the numbers are not exist at same count in the text
        for number in numbers:
            if product_name.count(number) < search.count(number):
                return False

        # not suitable if the words are not exist at same count in the text
        for word in _search:
            normalized_word = normalizer.sub('', word).lower()
            if product_name.count(normalized_word) < search.count(word):
                return False
        return True

    def check_the_suitability(self, product_name, searches):
        if not isinstance(searches, list):
            searches = [searches]
        return any([
            self.is_suitable_to_search(product_name, search)
            for search in searches
        ])

    @staticmethod
    def _parse_numbers(text):
        return re.findall(r'\d+', text)

    @staticmethod
    def bs_select(soup, dictionary, attribute_path):
        selector = get_attribute_by_path(
            dictionary, f"{attribute_path}.selector"
        )
        function = selector and getattr(soup, selector['type'], None)
        return function and function(*selector['args'], **selector['kwargs'])

    @staticmethod
    def get_text(element):
        """
        it will parse the text of element without children's
        returns the whole texts if no text found
        """
        text = ''.join(element.find_all(text=True, recursive=False)).strip()
        return text or element.text

    def get_page_number(self, soup):
        def get_value(el):
            key = self.source['page_number'].get('key')
            return key and el[key] or self.get_text(el)

        result = self.bs_select(soup, self.source, 'page_number')
        values = []

        if not result:
            return self.max_page

        if not isinstance(result, ResultSet):
            result = [result]

        for element in result:
            trimmed = get_value(element).replace(',', '').replace('.', '')
            numbers = map(int, self._parse_numbers(trimmed))
            try:
                values.append(self.pagination_method(numbers))
            except ValueError as exc:
                logging.error(
                    "Couldn't find any number in {}. Exc: {}".format(
                        result, exc.__repr__()
                    )
                )

        page = values and max(values)
        return page and page > self.max_page and self.max_page or page

    @staticmethod
    def get_normalized_response(response):
        return BeautifulSoup(response.content, 'lxml')

    def is_response_ok(self, soup):
        return self.bs_select(
            soup, self.source, 'validations.is_listing_page'
        )

    def set_pre_results(self, urls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bulk_req = asyncio.ensure_future(
            self.get_page_contents([url['url'] for url in urls])
        )
        responses = loop.run_until_complete(bulk_req)
        for url, response in zip(urls, responses):
            normalized_response = self.get_normalized_response(response)
            if normalized_response and self.is_response_ok(normalized_response):
                page_number = self.get_page_number(normalized_response)
                url['products'] = self.get_products(
                    normalized_response, url['search']
                )
                if page_number > 1:
                    url['start_page'] = self.first_page + 1
                    url['end_page'] = page_number + (self.first_page - 1)
                else:
                    url['start_page'] = None
                    url['end_page'] = None
            else:
                url['products'] = []
                url['start_page'] = None
                url['end_page'] = None

    # @log_time(fake_args=['source'])
    def get_results(self, urls):
        generated_urls = []
        products = []
        for url in urls:
            if not (url.get('start_page') and url.get('end_page')):
                continue
            for generated_url in self.generate_paginated_urls(
                    url['url'], url['start_page'], url['end_page']
            ):
                generated_urls.append(
                    {
                        'url': generated_url,
                        'search': url['search']
                    }
                )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bulk_req = asyncio.ensure_future(
            self.get_page_contents([url['url'] for url in generated_urls])
        )
        responses = loop.run_until_complete(bulk_req)
        for generated_url, response in zip(generated_urls, responses):
            normalized_response = self.get_normalized_response(response)
            products += self.get_products(
                normalized_response, generated_url['search']
            )
        return products

    # @log_time(log_args=False, log_kwargs=False)
    def filter_results(self, results):
        seen = set()
        filtered_results = []
        for item in sorted(results, key=lambda i: not i['suitable_to_search']):
            if item['hash'] in seen:
                continue
            else:
                filtered_results.append(item)
                seen.add(item['hash'])
        return filtered_results

    @log_time(fake_args=['source'])
    def search(self, category, search, urls=None):
        results = []
        # multiple results if search has list
        urls = urls or self.get_urls(category, search)
        self.set_pre_results(urls)
        for url in urls:
            results += url.pop('products', [])
        results += self.get_results(urls)
        results = self.filter_results(results)
        return results

    def parse_products(self, soup):
        return self.bs_select(soup, self.source, f"product.listing")

    def get_value(self, parsed_product, key_path):
        return self.bs_select(parsed_product, self.attributes, key_path)

    # @log_time(log_args=False, log_kwargs=False)
    def get_products(self, normalized_response, search):
        products = []

        for product in self.parse_products(normalized_response):
            acceptable = True
            data = {'source': self.name}
            for attribute_name, attribute_config in self.attributes.items():
                is_required = attribute_config.get('required')
                function = attribute_config['listing']['function']
                key_path = f"{attribute_name}.listing"
                parsed_value = self.get_value(product, key_path)
                value_key = attribute_config['listing'].get('key')
                normalized_value = getattr(self, function)(
                    parsed_value, key=value_key
                )
                data[attribute_name] = normalized_value
                if is_required and not data[attribute_name]:
                    acceptable = False
            if acceptable:
                data['suitable_to_search'] = self.check_the_suitability(
                    data['name'], search
                )
                self.add_hash(data, keys=['name', 'price'])
                products.append(data)
        return products

    def add_hash(self, product, keys=None):
        keys = keys or product.keys()
        hash = hashlib.md5()
        content = [product.get(key) for key in keys]
        encoded = json.dumps(content, sort_keys=True).encode()
        hash.update(encoded)
        product['hash'] = hash.hexdigest()

    def get_product_name(self, result, key=None):
        def get_value(el):
            return key and el[key] or el.text

        if not result:
            return

        if not isinstance(result, ResultSet):
            result = [result]

        return ' '.join(map(lambda i: ' '.join(get_value(i).split()), result))

    def get_product_price(self, result, key=None):
        def get_value(el):
            return key and el[key] or self.get_text(el)

        if not result:
            return

        if not isinstance(result, ResultSet):
            result = [result]

        prices = {
            int(price.amount) for price in
            [
                Price.fromstring(get_value(item)) for item in result
                if item
            ]
            if price.amount
        }
        return prices and min(prices)

    def get_product_info(self, result, key=None):
        def get_value(el):
            return key and el[key] or el.text

        if not result:
            return

        if not isinstance(result, ResultSet):
            result = [result]

        return ' '.join(map(lambda i: ' '.join(get_value(i).split()), result))

    def get_product_comment_count(self, result, key=None):
        def get_value(el):
            return key and el[key] or el.text

        if not result:
            return

        if not isinstance(result, ResultSet):
            result = [result]

        return ' '.join(map(lambda i: ' '.join(get_value(i).split()), result))

    def get_discount_calculated(self, result, key=None):
        def get_value(el):
            return key and el[key] or self.get_text(el)

        if not result:
            return

        if not isinstance(result, ResultSet):
            result = [result]

        prices = {
            int(price.amount) for price in
            [
                Price.fromstring(get_value(item)) for item in result
                if item
            ]
            if price.amount
        }

        min_val = min(prices)
        max_val = max(prices)
        return min_val != max_val and (max_val - min_val) / max_val * 100
