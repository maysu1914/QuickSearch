import re
from ast import literal_eval
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import urlparse

from colorit import init_colorit, background, color

from cli_prompts import Prompt
from scraper.models import Scraper
from scraper.utils import get_attribute_by_path, log_time

EXECUTOR = ThreadPoolExecutor(max_workers=32)

init_colorit()


class PromptURL(Prompt):

    def is_valid(self):
        # https://regexr.com/39nr7
        regex = r'[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
        if self._data and re.match(regex, self._data):
            hostname = urlparse(self._data).hostname
            if self.choices:
                if hostname in self.choices.values():
                    self._valid = True
                else:
                    self._valid = False
            else:
                self._valid = True
        else:
            self._valid = False
        return self._valid

    def render(self):
        title = self._get_title()
        if title:
            print(title)


class PromptSource(Prompt):

    def _normalize_data(self):
        try:
            source_selections = {s for s in self._data.split(',')}
            if '0' in source_selections:
                source_selections.update(self.choices.keys())
                source_selections.discard('0')
            source_selections = {int(i) for i in source_selections}
            negatives = set([i for i in source_selections if i < 0])
            discarded_positives = set([abs(i) for i in negatives])
            source_selections -= negatives | discarded_positives
            source_selections = {str(i) for i in source_selections}
            self._data = source_selections
        except ValueError:
            pass

    def is_valid(self):
        data = self._data
        if self.choices:
            if data and set(data).issubset(set(self.choices.keys())):
                self._valid = True
        else:
            self._valid = True
        return self._valid

    @property
    def data(self):
        if self._valid:
            if self.choices and not self._raw_data:
                return [self.choices[i] for i in self._data]
            else:
                return self._data
        else:
            raise ValueError('the data is not valid')


class QuickSearch:

    def __init__(self, config, max_page=None):
        self.config = config
        self.sources = config['sources']
        self.max_page = max_page

    def get_search_types(self):
        search_types = (
            'By entering the categories, sources, and a search text.',
            'By entering a URL and a search text.'
        )
        return search_types

    def get_categories(self):
        categories = []
        for source in self.sources:
            for category in source.get('categories'):
                if category not in categories:
                    categories.append(category)
        return categories

    def get_hostnames(self):
        hostnames = []
        for source in self.sources:
            hostname = urlparse(source.get('base_url')).hostname
            hostnames.append(hostname)
        return hostnames

    def get_source_by_url(self, url):
        if not getattr(url, 'hostname', None):
            url = urlparse(url)
        for source in self.sources:
            base_url = urlparse(source.get('base_url'))
            if base_url.hostname == url.hostname:
                return source

    @lru_cache
    def get_sources_of_category(self, category):
        sources = [
            {
                'name': 'All',
                'style': {
                    'bg_color': '(255, 255, 255)',
                    'fg_color': '(0, 0, 0)'
                }
            }
        ]
        for source in self.sources:
            if category in source.get('categories'):
                sources.append(source)
        return sources

    def get_style(self, source_name, attribute):
        if isinstance(source_name, dict):
            return get_attribute_by_path(source_name, f"style.{attribute}")
        else:
            for source in self.sources:
                if source.get('name') == source_name:
                    return source['style'][attribute]
            else:
                return None

    def get_search_type_input(self, data=None):
        choices = self.get_search_types()
        title = 'Which way do you prefer to search with?'
        prompt = 'Search Type: '

        prompt = Prompt(title=title, prompt=prompt, choices=choices, data=data)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_category_input(self, data=None):
        choices = self.get_categories()
        title = '\nWhat category do you want to search?'
        prompt = 'Category: '

        prompt = Prompt(title=title, prompt=prompt, choices=choices, data=data,
                        raw_data=False)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_source_input_by_category(self, category):
        sources = self.get_sources_of_category(category)
        choices = []
        for source in sources:
            bg_color = literal_eval(self.get_style(source, 'bg_color'))
            fg_color = literal_eval(self.get_style(source, 'fg_color'))
            choices.append(
                background(color(f" {source['name']} ", fg_color), bg_color)
            )

        title = '\nSelect the sources you want to search:'
        prompt = 'Sources: '

        prompt = PromptSource(
            title=title, prompt=prompt, choices=choices
        )
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_url_input(self, data=None):
        choices = self.get_hostnames()
        title = '\nWhich URL you want to search?'
        prompt = 'The url: '

        prompt = PromptURL(
            title=title, prompt=prompt, choices=choices, data=data
        )
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_search_input(self):
        search_input = input('\nSearch Text: ').strip()
        return search_input

    def get_max_page_input(self):
        try:
            max_page_input = int(input('(Optional) Max page limit: '))
        except ValueError:
            max_page_input = None

        return max_page_input

    def start(self):
        search_type = self.get_search_type_input()
        max_page = self.get_max_page_input() or self.max_page

        if search_type == '0':
            category = self.get_category_input()
            sources = self.get_source_input_by_category(category)
            search_text = self.get_search_input()
            results = self.get_results(sources, category, search_text, max_page)
        else:
            url = self.get_url_input()
            source = self.get_source_by_url(url)
            search_text = self.get_search_input()
            results = self.get_results_by_url(
                url, source, search_text, max_page
            )

        correct_results, near_results = self.divide_results(results)
        self.show_results(correct_results, near_results)

    @log_time()
    def get_results(self, sources, category, search_text, max_page):
        threads = []
        results = []

        category_sources = self.get_sources_of_category(category)
        for source_selection in sources:
            source = category_sources[int(source_selection)]
            scraper = Scraper(source, max_page=max_page)
            thread = EXECUTOR.submit(scraper.search, category, search_text)
            threads.append(thread)

        for thread in futures.as_completed(threads):
            results += thread.result()

        return results

    @log_time()
    def get_results_by_url(self, url, source, search_text, max_page):
        scraper = Scraper(source, max_page=max_page)
        combinations = scraper.get_all_combinations(search_text)
        results = scraper.get_results({'url': url, 'search': combinations})
        return results

    @staticmethod
    def divide_results(results):
        correct_results = []
        near_results = []
        results = sorted(results, key=lambda i: (i['price'] == 0, i['price']))

        for item in results:
            if item.get('suitable_to_search'):
                correct_results.append(item)
            else:
                near_results.append(item)
        return correct_results, near_results

    def show_results(self, correct_results, near_results):
        if correct_results:
            print('\nResults:')
            self._show_results(correct_results)
        if near_results:
            print('\nYou may want to look at these:')
            self._show_results(near_results)

    def get_styled_text(self, text, fg_color=None, bg_color=None):
        text = fg_color and color(text, fg_color) or text
        text = bg_color and background(text, bg_color) or text
        return text

    def get_fixed_size_text(self, text, size):
        pre_space = int((size - len(text)) / 2)
        post_space = size - (len(text) + pre_space)
        return "%s%s%s" % (pre_space * ' ', text, post_space * ' ')

    def _show_results(self, results):
        price_style = ((255, 255, 255), (0, 128, 0),)
        for product in results:
            source = self.get_styled_text(
                self.get_fixed_size_text(product['source'], 16),
                literal_eval(self.get_style(product['source'], 'fg_color')),
                literal_eval(self.get_style(product['source'], 'bg_color'))
            )
            name = product['name']
            currency = 'TL'
            price = product['price'] and "%s %s" % (product['price'], currency)
            info = product.get('info')
            comment_count = product.get('comment_count')
            discount = product.get('discount')

            line = "%s %s • %s • %s • %s • %s" % (
                source,
                name,
                self.get_styled_text(price or 'Fiyat Yok', *price_style),
                info or '',
                comment_count or '',
                discount and "%%%s indirim" % discount or ''
            )
            print(line)
