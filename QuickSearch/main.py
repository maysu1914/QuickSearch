from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from colorit import *

from QuickSearch.ui.ui import PromptUI, PromptURL, PromptCategory
from scraper.scraper import Scraper

init_colorit()


class QuickSearch:
    name = "QuickSearch"
    max_page = 3

    def __init__(self, config, max_page=max_page):
        self.config = config
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()

        self.search_type_selection = None

        self.url_input = None
        self.url_source = None

        self.category_selection = None
        self.source_selections = []
        self.search_text = None
        self.raw_results = []
        self.correct_results = []
        self.near_results = []

    @property
    def search_types(self):
        search_types = (
            'By entering the categories, sources, and a search text.',
            'By entering a URL and a search text.')
        return search_types

    @property
    def categories(self):
        categories = []
        for source in self.config.get("sources"):
            for category in source.get("categories"):
                if category not in categories:
                    categories.append(category)
        return categories

    @property
    def hostnames(self):
        hostnames = []
        for source in self.config.get("sources"):
            hostname = urlparse(source.get("base_url")).hostname
            hostnames.append(hostname)
        return hostnames

    def get_search_type_input(self):
        choices = self.search_types
        title = 'Which way do you prefer to search with?'
        prompt = 'Search Type: '

        prompt = PromptUI(title=title, prompt=prompt, choices=choices)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_category_input(self):
        choices = self.categories
        title = '\nWhat category do you want to search?'
        prompt = 'Category: '

        prompt = PromptUI(title=title, prompt=prompt, choices=choices,
                          raw_data=False)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return prompt.data

    def get_source_input_by_category(self):
        sources = self.get_sources_of_category(self.category_selection)
        choices = []
        for source in sources:
            bg_color = literal_eval(self.get_style(source["name"], "bg_color"))
            fg_color = literal_eval(self.get_style(source["name"], "fg_color"))
            choices.append(background(color(f" {source['name']} ", fg_color), bg_color))
        choices.insert(0, background(color(f" All ", (0, 0, 0)), (255, 255, 255)))

        title = '\nSelect the sources you want to search:'
        prompt = 'Sources: '

        prompt = PromptCategory(title=title, prompt=prompt, choices=choices,
                                raw_data=True)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        return [int(i) - 1 for i in prompt.data]

    def get_url_input(self):
        choices = self.hostnames
        title = '\nWhich URL you want to search?'
        prompt = 'The url: '

        prompt = PromptURL(title=title, prompt=prompt, choices=choices)
        prompt.render()

        while not prompt.is_valid():
            prompt.get_input()

        url_source = self.get_source_of_url(urlparse(prompt.data))
        return prompt.data, url_source

    def get_search_input(self):
        search_input = input('\nSearch Text: ').strip()
        return search_input

    def get_max_page_input(self):
        try:
            max_page_input = int(input('(Optional) Max page limit: '))
        except ValueError:
            max_page_input = None

        return max_page_input if max_page_input else self.max_page

    def get_source_of_url(self, url):
        for source in self.config.get("sources"):
            if urlparse(source.get("base_url")).hostname == getattr(url, "hostname", None):
                return source
        else:
            return None

    def get_sources_of_category(self, category):
        sources = []
        for source in self.config.get("sources"):
            if category in source.get("categories"):
                sources.append(source)
        return sources

    def start(self, search_type=None):
        self.search_type_selection = self.get_search_type_input() if not search_type else search_type
        if self.search_type_selection == '0':
            self.category_selection = self.get_category_input()
            self.source_selections = self.get_source_input_by_category()
            self.search_text = self.get_search_input()
            self.max_page = self.get_max_page_input()
            self.get_results()
            self.set_results()
            self.show_results()
        if self.search_type_selection == '1':
            self.url_input, self.url_source = self.get_url_input()
            self.search_text = self.get_search_input()
            self.max_page = self.get_max_page_input()
            self.get_results_from_url()
            self.set_results()
            self.show_results()

    def get_results(self):
        threads = []
        sources = self.get_sources_of_category(self.category_selection)

        for source_selection in self.source_selections:
            args = (sources[source_selection],)
            kwargs = {"max_page": self.max_page}
            thread = self.executor.submit(Scraper(*args, **kwargs).search, self.category_selection, self.search_text)
            threads.append(thread)

        for thread in threads:
            self.raw_results += thread.result()

    def get_results_from_url(self):
        args = (self.url_source,)
        kwargs = {"max_page": self.max_page}
        searches = Scraper.get_all_combinations(self.search_text)
        self.raw_results += Scraper(*args, **kwargs).get_results(
            {'url': self.url_input, 'search': searches})

    def get_style(self, name, attribute):
        for source in self.config["sources"]:
            if source.get("name") == name:
                return source["style"][attribute]
        else:
            return None

    def set_results(self):
        # sort results by price and suitable_to_search values
        # (True value is first after than low price)
        self.raw_results = sorted(self.raw_results,
                                  key=lambda i: (i['price'] == 0, i['price'], -i['suitable_to_search']))

        unique_results = []
        seen = set()  # to skip same products from different results

        for result in self.raw_results:
            r = (result['source'], result['name'], result['price'])
            # check above data only for duplicate check
            if r not in seen:
                seen.add(r)
                unique_results.append(result)

        for result in unique_results:
            if result.get('suitable_to_search'):
                self.correct_results.append(result)
            else:
                self.near_results.append(result)

    def show_results(self):
        print("\nResults:") if self.correct_results else ''
        for product in self.correct_results:
            bg_color = literal_eval(self.get_style(product['source'], "bg_color"))
            fg_color = literal_eval(self.get_style(product['source'], "fg_color"))
            print(background(color(f" {product['source']} ", fg_color), bg_color), end=' ')
            data = (
                product['name'],
                str(product['price']) + ' TL' if product.get('price') else 'Fiyat Yok',
                product['info'] if product.get('info') else '',
                product['comment_count'] if product.get('comment_count') else ''
            )
            print(' • '.join(data))

        print("\nYou may want to look at these:") if self.near_results else ''
        for product in self.near_results:
            bg_color = literal_eval(self.get_style(product['source'], "bg_color"))
            fg_color = literal_eval(self.get_style(product['source'], "fg_color"))
            print(background(color(f" {product['source']} ", fg_color), bg_color), end=' ')
            data = (
                product['name'],
                str(product['price']) + ' TL' if product.get('price') else 'Fiyat Yok',
                product['info'] if product.get('info') else '',
                product['comment_count'] if product.get('comment_count') else ''
            )

            print(' • '.join(data))
        print("_________________________________\n")
