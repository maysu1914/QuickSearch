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
        return get_attribute_by_path(self.source, 'page_number.first_page',
                                     self.default_first_page)

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
        product_name = product_name.lower()
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
            if product_name.count(word) < search.count(word):
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
    def bs_select(soup, dictionary, attribute_path):
        selector = get_attribute_by_path(dictionary,
                                         f"{attribute_path}.selector")
        return selector and getattr(soup, selector['type'])(
            *selector['args'], **selector['kwargs']
        )

    @staticmethod
    def get_text(element):
        """
        it will parse the text of element without children's
        returns the whole texts if no text found
        """
        text = ''.join(element.find_all(text=True, recursive=False)).strip()
        return text or element.text

    @staticmethod
    def _parse_numbers(text):
        return re.findall(r'\d+', text)

    def get_page_number(self, result):
        if result and isinstance(result, ResultSet):
            numbers = [self.get_page_number(e) for e in result]
            return max(numbers)
        elif result:
            page = self.max_page
            trimmed = result.text.replace(',', '').replace('.', '')
            numbers = map(int, self._parse_numbers(trimmed))
            products_per_page = self.source['page_number']['products_per_page']
            method = self.source['page_number']['method']
            try:
                if method == 'total':
                    page = math.ceil(max(numbers) / products_per_page)
                elif method == 'pagination':
                    page = max(numbers)
            except ValueError as exc:
                logging.error(
                    "Couldn't fine any number in {}. Exc: {}".format(
                        result, exc.__repr__()
                    )
                )
            return page > self.max_page and self.max_page or page
        else:
            return self.max_page

    def set_pre_results(self, urls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bulk_req = asyncio.ensure_future(
            self.get_page_contents([url['url'] for url in urls])
        )
        responses = loop.run_until_complete(bulk_req)
        for url, response in zip(urls, responses):
            soup = BeautifulSoup(response.content, 'lxml')
            is_listing_page = self.bs_select(
                soup, self.source, 'validations.is_listing_page'
            )
            if soup and is_listing_page:
                page_number = self.get_page_number(
                    self.bs_select(soup, self.source, 'page_number')
                )
                url['products'] = self.get_products(
                    response.content, url['search'], 'listing'
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
            products += self.get_products(
                response.content, generated_url['search'], 'listing'
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

    # @log_time(log_args=False, log_kwargs=False)
    def get_products(self, content, search, page_type):
        soup = BeautifulSoup(content, 'lxml')
        products = []

        for product in self.bs_select(soup, self.source, f"product.{page_type}"):
            acceptable = True
            data = {'source': self.name}
            for key, value in self.attributes.items():
                function = value[page_type]['function']
                key_path = f"{key}.{page_type}"
                data[key] = getattr(self, function)(self.bs_select(product, self.attributes, key_path))
                if value.get('required') and not data[key]:
                    acceptable = False
            if acceptable:
                data['suitable_to_search'] = self.check_the_suitability(
                    data['name'], search
                )
                products.append(self.add_hash(data, keys=['name', 'price']))
        return products

    def add_hash(self, product, keys=None):
        keys = keys or product.keys()
        hash = hashlib.md5()
        encoded = json.dumps([product.get(key) for key in keys], sort_keys=True).encode()
        hash.update(encoded)
        product['hash'] = hash.hexdigest()
        return product

    def get_product_name(self, result):
        if isinstance(result, ResultSet):
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None

    def get_product_price(self, result):
        if isinstance(result, ResultSet):
            numbers = [''.join([s for s in self.get_text(e).split(',')[0] if s.isdigit()]) for e in result]
            numbers = [int(number) for number in numbers if number]
            return min(numbers) if numbers else 0
        elif result:
            number = ''.join([s for s in result.text.split(',')[0] if s.isdigit()])
            return int(number) if number else 0
        else:
            return 0

    def get_product_info(self, result):
        if isinstance(result, ResultSet):
            return ', '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None

    def get_product_comment_count(self, result):
        if isinstance(result, ResultSet):
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
        elif result:
            return ' '.join(result.text.split())
        else:
            return None

    def get_discount_calculated(self, result):
        if isinstance(result, ResultSet):
            numbers = [''.join([s for s in self.get_text(e).split(',')[0] if s.isdigit()]) for e in result]
            values = [int(number) for number in numbers] if numbers and all(numbers) else [0]
            min_val = min(values)
            max_val = max(values)
            return int((max_val - min_val) / max_val * 100) if min_val != max_val else 0
        else:
            return 0
