import hashlib
import itertools
import json
import math
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from requests.utils import requote_uri

from scraper.mixins import RequestMixin, ToolsMixin
from scraper.utils import get_attribute_by_path


class Scraper(ToolsMixin, RequestMixin):
    default_first_page = 1

    def __init__(self, source, *args, **kwargs):
        super(Scraper, self).__init__(source, *args, **kwargs)
        self.source = source
        self.max_page = kwargs.get('max_page', 3)
        self.driver = None

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
        return get_attribute_by_path(self.source, 'page_number.first_page', self.default_first_page)

    def search(self, category, search):
        error_count = 0
        results = []
        urls = self.get_urls(category, search)  # multiple results if search has list
        for url in urls:
            try:
                results += self.get_results(url)
            except requests.exceptions.RequestException as e:
                error_count += 1
                if error_count >= math.ceil(len(urls) / 4):
                    print(f"Too much error occurred in {self.name}", e)
                    break
        results = self.filter_results(results)
        return results

    def get_urls(self, category, search):
        categories = self.source.get('categories')
        urls = []

        if category in categories:
            for search_text in self.get_all_combinations(search):
                url = self.create_url(search_text, categories[category])
                urls.append({'search': search_text, 'url': requote_uri(url)})
        return urls

    def generate_paginated_urls(self, url, start_page, end_page):
        for number in range(start_page, end_page):
            yield self.prepare_url(url, self.pagination_query % number)

    def get_all_combinations(self, search):
        searches = []
        if '[' in search and ']' in search:
            static = search
            dynamic = []

            for a, b in zip(range(1, search.count('[') + 1), range(1, search.count(']') + 1)):
                start = self.find_nth(search, '[', a)
                end = self.find_nth(search, ']', a) + 1
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

        search_numbers = re.findall(r'\d+', search)
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
        return getattr(soup, selector['type'])(*selector['args'], **selector['kwargs']) if selector else None

    @staticmethod
    def get_text(element):
        """
        it will parse the text of element without children's
        returns the whole texts if no text found
        """
        text = ''.join(element.find_all(text=True, recursive=False)).strip()
        return text or element.text

    def get_results(self, url):
        content = next(self.get_page_contents([url.get('url')]))
        soup = BeautifulSoup(content, 'lxml')
        results = []
        if soup and self.bs_select(soup, self.source, 'validations.is_listing_page'):
            page_number = self.get_page_number(self.bs_select(soup, self.source, 'page_number'))
            results += self.get_products(content, url['search'], 'listing')
            if page_number > 1:
                start_page = self.first_page + 1
                end_page = self.first_page + page_number
                url_generator = self.generate_paginated_urls(url['url'], start_page, end_page)
                contents = self.get_page_contents(url_generator)
                for content in contents:
                    results += self.get_products(content, url['search'], 'listing')
            else:
                pass
        else:
            pass
        return results

    def filter_results(self, results):
        seen = set()
        filtered_results = []
        for item in results:
            if item['hash'] in seen:
                continue
            else:
                filtered_results.append(item)
                seen.add(item['hash'])
        return filtered_results

    def get_page_number(self, result):
        if result and isinstance(result, ResultSet):
            numbers = [max(map(int, re.findall(r'\d+', e.text))) for e in result if any(re.findall(r'\d+', e.text))]
            page = max(numbers)
            return self.max_page if page > self.max_page else page
        elif result:
            numbers = tuple(map(int, re.findall(r'\d+', result.text.replace(',', '').replace('.', ''))))
            page = math.ceil(max(numbers) / self.source['page_number']['products_per_page']) if numbers else 1
            return self.max_page if page > self.max_page else page
        else:
            return 1

    def create_url(self, search, category):
        url = urljoin(self.base_url, self.query['path'])
        search = self.query['space'].join(search.split())
        category = category.format(search=search) if self.is_formattable(category) else category
        return url % {'category': category, 'search': search}

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
            data['suitable_to_search'] = self.check_the_suitability(data['name'], search)
            if acceptable:
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
            return ' '.join(map(lambda i: ' '.join(i.text.split()), result))
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
