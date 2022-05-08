from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import urlparse

from colorit import init_colorit, background, color

from cli_prompts import PromptUI, PromptURL, PromptSource
from scraper.scraper import Scraper
from scraper.utils import get_attribute_by_path

init_colorit()


class QuickSearch:
    name = 'QuickSearch'

    def __init__(self, config, search_type=None, url=None, category=None,
                 sources=None, search_text=None, max_page=None,
                 thread_pool_executor=None):
        self.config = config
        if not isinstance(thread_pool_executor, ThreadPoolExecutor):
            self.executor = ThreadPoolExecutor()
        else:
            self.executor = thread_pool_executor

        self.search_type = search_type
        self.url = url
        self.category = category
        self.sources = sources
        self.search_text = search_text
        self.max_page = max_page

    @property
    def search_types(self):
        search_types = (
            'By entering the categories, sources, and a search text.',
            'By entering a URL and a search text.')
        return search_types

    @property
    def categories(self):
        categories = []
        for source in self.config.get('sources'):
            for category in source.get('categories'):
                if category not in categories:
                    categories.append(category)
        return categories

    @property
    def hostnames(self):
        hostnames = []
        for source in self.config.get('sources'):
            hostname = urlparse(source.get('base_url')).hostname
            hostnames.append(hostname)
        return hostnames

    def get_source_of_url(self, url):
        for source in self.config.get('sources'):
            if urlparse(source.get('base_url')).hostname == getattr(url, 'hostname', None):
                return source
        else:
            return None

    @lru_cache
    def get_sources_of_category(self, category):
        sources = [{'name': 'All', 'style': {'bg_color': '(255, 255, 255)', 'fg_color': '(0, 0, 0)'}}]
        for source in self.config.get('sources'):
            if category in source.get('categories'):
                sources.append(source)
        return sources

    def get_style(self, source_name, attribute):
        if isinstance(source_name, dict):
            return get_attribute_by_path(source_name, f"style.{attribute}")
        else:
            for source in self.config['sources']:
                if source.get('name') == source_name:
                    return source['style'][attribute]
            else:
                return None

    def get_search_type_input(self, data=None):
        choices = self.search_types
        title = 'Which way do you prefer to search with?'
        prompt = 'Search Type: '

        prompt = PromptUI(title=title, prompt=prompt, choices=choices, data=data)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_category_input(self, data=None):
        choices = self.categories
        title = '\nWhat category do you want to search?'
        prompt = 'Category: '

        prompt = PromptUI(title=title, prompt=prompt, choices=choices, data=data,
                          raw_data=False)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_source_input_by_category(self, data=None):
        sources = self.get_sources_of_category(self.category)
        choices = []
        for source in sources:
            bg_color = literal_eval(self.get_style(source, 'bg_color'))
            fg_color = literal_eval(self.get_style(source, 'fg_color'))
            choices.append(background(color(f" {source['name']} ", fg_color), bg_color))

        title = '\nSelect the sources you want to search:'
        prompt = 'Sources: '

        prompt = PromptSource(title=title, prompt=prompt, choices=choices, data=data)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_url_input(self, data=None):
        choices = self.hostnames
        title = '\nWhich URL you want to search?'
        prompt = 'The url: '

        prompt = PromptURL(title=title, prompt=prompt, choices=choices, data=data)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        source = self.get_source_of_url(urlparse(prompt.data))
        return prompt.data, [source]

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
        self.search_type = self.get_search_type_input(data=self.search_type)
        if self.search_type == '0':
            self.category = self.get_category_input(data=self.category)
            self.sources = self.get_source_input_by_category(data=self.sources)
        elif self.search_type == '1':
            self.url, self.sources = self.get_url_input(data=self.url)
        else:
            raise NotImplementedError('unknown type of %s' % self.search_type)

        self.search_text = self.search_text or self.get_search_input()
        self.max_page = self.get_max_page_input() or self.max_page
        self.process()

    def process(self):
        if self.search_type == '0':
            correct_results, near_results = self.divide_results(self.results)
        elif self.search_type == '1':
            correct_results, near_results = self.divide_results(self.results_from_url)
        else:
            raise NotImplementedError('unknown type of %s' % self.search_type)
        self.show_results(correct_results, near_results)

    @property
    def results(self):
        sources = self.get_sources_of_category(self.category)
        threads = []
        results = []

        for source_selection in self.sources:
            source = sources[int(source_selection)]
            scraper = Scraper(source, max_page=self.max_page)
            thread = self.executor.submit(scraper.search, self.category, self.search_text)
            threads.append(thread)

        for thread in threads:
            results += thread.result()

        return results

    @property
    def results_from_url(self):
        scraper = Scraper(self.sources[0], max_page=self.max_page)
        combinations = scraper.get_all_combinations(self.search_text)
        results = scraper.get_results({'url': self.url, 'search': combinations})
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

    def _show_results(self, results):
        for product in results:
            bg_color = literal_eval(self.get_style(product['source'], 'bg_color'))
            fg_color = literal_eval(self.get_style(product['source'], 'fg_color'))
            print(background(color(f" {product['source']} ", fg_color), bg_color), end=' ')
            data = (
                product['name'],
                str(product['price']) + ' TL' if product.get('price') else 'Fiyat Yok',
                product['info'] if product.get('info') else '',
                product['comment_count'] if product.get('comment_count') else ''
            )
            print(' • '.join(data))
