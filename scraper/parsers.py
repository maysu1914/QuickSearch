import logging
import math

from bs4 import BeautifulSoup, ResultSet
from price_parser import Price

from scraper.mixins import RequestMixin
from scraper.utils import get_attribute_by_path, parse_numbers


class Parser(RequestMixin):

    def __init__(self, source, max_page):
        super().__init__(source)
        self.source = source
        self.max_page = max_page

    def is_response_ok(self, normalized_response):
        raise NotImplementedError

    @staticmethod
    def get_normalized_response(response):
        raise NotImplementedError

    def get_page_number(self, normalized_response):
        raise NotImplementedError

    def parse_products(self, normalized_response):
        raise NotImplementedError

    def get_product_attribute_value(self, product, name, config):
        raise NotImplementedError

    def get_product_name(self, *args, **kwargs):
        raise NotImplementedError

    def get_product_price(self, *args, **kwargs):
        raise NotImplementedError

    def get_product_info(self, *args, **kwargs):
        raise NotImplementedError

    def get_product_comment_count(self, *args, **kwargs):
        raise NotImplementedError

    def get_discount_calculated(self, *args, **kwargs):
        raise NotImplementedError


class HtmlParser(Parser):

    @property
    def products_per_page(self):
        return self.source['page_number']['products_per_page']

    @property
    def pagination_method(self):
        method = self.source['page_number']['method']
        return getattr(self, 'get_page_from_{}'.format(method))

    def get_page_from_total(self, value):
        return math.ceil(value / self.products_per_page)

    def get_page_from_pagination(self, value):
        return value

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

    def is_response_ok(self, soup):
        return soup and self.bs_select(
            soup, self.source, 'validations.is_listing_page'
        )

    @staticmethod
    def get_normalized_response(response):
        return BeautifulSoup(response.content, 'lxml')

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
            numbers = map(int, parse_numbers(trimmed))
            try:
                values.append(self.pagination_method(max(numbers)))
            except ValueError as exc:
                logging.error(
                    "Couldn't find any number in {}. Exc: {}".format(
                        result, exc.__repr__()
                    )
                )

        page = values and max(values)
        return page and page > self.max_page and self.max_page or page

    def parse_products(self, soup):
        return self.bs_select(soup, self.source, f"product.listing")

    def get_value(self, parsed_product, config, key_path):
        return self.bs_select(parsed_product, config, key_path)

    def get_product_attribute_value(self, product, name, config):
        function = config['listing']['function']
        parsed_value = self.get_value(product, config, 'listing')
        value_key = config['listing'].get('key')
        return getattr(self, function)(
            parsed_value, key=value_key
        )

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
