from ast import literal_eval
from urllib.parse import urlparse

from colorit import *

init_colorit()

from scraper.scraper import *


class QuickSearch:
    max_page = 3
    name = "QuickSearch"

    def __init__(self, config, max_page=max_page):
        self.config = config
        self.categories = self.get_categories()
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()

        self.search_type_selection = None

        self.url_input = None
        self.url_source = None

        self.category_selection = None
        self.sources_of_category = []
        self.source_selections = []
        self.search_text = None
        self.raw_results = []
        self.correct_results = []
        self.near_results = []

    def get_categories(self):
        categories = []
        for source in self.config.get("sources"):
            for category in source.get("categories"):
                if category not in categories:
                    categories.append(category)
        return categories

    def get_search_type_input(self):
        search_types = [
            'By entering the categories, sources, and a search text.',
            'By entering a URL and a search text.'
        ]
        search_type_selection = None
        print("Which way do you prefer to search with?")

        for index, search_type in enumerate(search_types):
            print(str(index) + '.', search_type)

        while search_type_selection not in list(range(len(search_types))):
            try:
                search_type_selection = int(input('Search Type: ').strip())
            except ValueError:
                search_type_selection = None

        return search_type_selection

    def start(self, search_type=None):
        self.search_type_selection = self.get_search_type_input() if not search_type else search_type
        if self.search_type_selection == 0:
            self.category_selection = self.get_category_input()
            self.source_selections = self.get_source_input_by_categories()
            self.search_text = self.get_search_input()
            self.max_page = self.get_max_page_input()
            self.get_results()
            self.set_results()
            self.show_results()
        if self.search_type_selection == 1:
            self.url_input, self.url_source = self.get_url_input()
            self.search_text = self.get_search_input()
            self.max_page = self.get_max_page_input()
            self.get_results_from_url()
            self.set_results()
            self.show_results()

    def get_url_input(self):
        url_input = ""
        url_source = ""
        # https://regexr.com/39nr7
        regex = r"[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
        print("\nWhich URL you want to search?")

        while not (re.match(regex, url_input) and url_source):
            url_input = input('The url: ')
            url_source = self.get_source_of_url(urlparse(url_input))

        return url_input, url_source

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

    def get_category_input(self):
        category_selection = []
        print("\nWhat category do you want to search?")

        for index, category in enumerate(self.categories):
            print(str(index) + '.', category)

        while category_selection not in list(range(0, len(self.categories))):
            try:
                category_selection = int(input('Category: ').strip())
            except ValueError:
                category_selection = None

        return self.categories[category_selection]

    def get_source_input_by_categories(self):
        source_selections = []
        print("\nSelect the sources you want to search:")

        for source in self.config.get("sources"):
            if self.category_selection in source.get("categories"):
                self.sources_of_category.append(source)

        print(str(0) + '.', end=" ")
        print(background(color(" All ", (0, 0, 0)), (255, 255, 255)))
        for index, source in enumerate(self.sources_of_category, start=1):
            bg_color = literal_eval(self.get_style(source["name"], "bg_color"))
            fg_color = literal_eval(self.get_style(source["name"], "fg_color"))
            print(str(index) + '.', end=" ")
            print(background(color(f" {source['name']} ", fg_color), bg_color))

        while not source_selections:
            try:
                # make set to handle duplicate inputs
                source_selections = {int(source_selection) for source_selection in input('Sources: ').split(',')}
                # if All option is selected
                if 0 in source_selections:
                    # filter the selections to accept only negatives
                    # get positive of them by mapping
                    # make set to use set subtraction feature in the next code
                    # convert user selection numbers to indexes by subtracting 1
                    excludes = set(
                        map(lambda i: abs(i) - 1, filter(lambda i: True if i < 0 else False, source_selections)))
                    # add all sources by len and exclude the unwanted
                    source_selections = set(range(len(self.sources_of_category))) - set(excludes)
                else:
                    # don't accept exclusion if already precise selection made
                    # filter the selections to leave only positives
                    source_selections = filter(lambda i: True if i > 0 else False, source_selections)
                    # store the index rather than storing selection
                    source_selections = [source_selection - 1 for source_selection in source_selections]
                    # to trigger possible IndexError exception
                    [self.sources_of_category[source_selection] for source_selection in source_selections]
            except (ValueError, IndexError):
                source_selections = []

        return source_selections

    @staticmethod
    def get_search_input():
        search_input = input('\nSearch Text: ').strip()
        return search_input

    def get_results(self):
        threads = []

        for source_selection in self.source_selections:
            args = (self.sources_of_category[source_selection],)
            kwargs = {"max_page": self.max_page}
            thread = self.executor.submit(Scraper(*args, **kwargs).search, self.category_selection, self.search_text)
            threads.append(thread)

        for thread in threads:
            self.raw_results += thread.result()

    def get_results_from_url(self):
        args = (self.url_source,)
        kwargs = {"max_page": self.max_page}
        self.raw_results += Scraper(*args, **kwargs).get_results(
            {'url': self.url_input, 'search': self.search_text})

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
            if self.search_type_selection == 0:
                if result.get('suitable_to_search'):
                    self.correct_results.append(result)
                else:
                    self.near_results.append(result)
            else:
                data = (
                    result['name'],
                    result['info'] if result.get('info') else ''
                )
                if any(Scraper.is_suitable_to_search(' '.join(data).lower(), search) for search in
                       self.search_text.replace('[', "").replace(']', "").split(',')):
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
