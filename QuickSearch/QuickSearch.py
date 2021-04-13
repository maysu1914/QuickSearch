from concurrent.futures.thread import ThreadPoolExecutor
from concurrent import futures

from .websites.AmazonTR import AmazonTR
from .websites.FLO import FLO
from .websites.GittiGidiyor import GittiGidiyor
from .websites.HepsiBurada import HepsiBurada
from .websites.MediaMarktTR import MediaMarktTR
from .websites.N11 import N11
from .websites.Teknosa import Teknosa
from .websites.Trendyol import Trendyol
from .websites.VatanBilgisayar import VatanBilgisayar


class QuickSearch:
    max_page = 3

    def __init__(self, max_page=max_page):
        self.sources = (VatanBilgisayar, N11, HepsiBurada, Trendyol, AmazonTR, Teknosa, GittiGidiyor, MediaMarktTR, FLO)
        self.categories = self.get_categories()
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()

        self.category_selection = None
        self.sources_of_category = []
        self.source_selections = []
        self.search_text = None
        self.raw_results = []
        self.correct_results = []
        self.near_results = []

    def get_categories(self):
        categories = []
        for source in self.sources:
            for category in source.get_categories():
                if category not in categories:
                    categories.append(category)
        return categories

    def search(self):
        self.category_selection = self.get_category_input()
        self.source_selections = self.get_source_input()
        self.search_text = self.get_search_input()
        self.get_results()
        self.show_results()

    def get_category_input(self):
        category_selection = []
        print("What category do you want to search?")

        for index, category in enumerate(self.categories):
            print(str(index) + '.', category)

        while category_selection not in list(range(0, len(self.categories))):
            try:
                category_selection = int(input('Category: ').strip())
            except ValueError:
                category_selection = None

        return self.categories[category_selection]

    def get_source_input(self):
        source_selections = []
        print("\nSelect the sources you want to search:")

        for source in self.sources:
            if self.category_selection in source.get_categories():
                self.sources_of_category.append(source)

        print(str(0) + '.', 'All')
        for index, source in enumerate(self.sources_of_category, start=1):
            print(str(index) + '.', source.source_name)

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
            arguments = [self.category_selection]
            keyword_arguments = {"max_page": self.max_page}
            source_object = self.sources_of_category[source_selection]
            thread = self.executor.submit(source_object(*arguments, **keyword_arguments).search, self.search_text)
            threads.append(thread)

        for thread in threads:
            self.raw_results += thread.result()

        # sort results by price and suitable_to_search values
        # (True value is first after than low price)
        self.raw_results = sorted(self.raw_results,
                                  key=lambda i: (int(i['price'].split()[0]), -i['suitable_to_search']))

        unique_results = []
        seen = set()  # to skip same products from different results

        for result in self.raw_results:
            r = (result['source'], result['name'], result['price'], result['info'])
            # check above data only for duplicate check
            if r not in seen:
                seen.add(r)
                unique_results.append(result)

        for result in unique_results:
            if result['suitable_to_search']:
                self.correct_results.append(result)
            else:
                self.near_results.append(result)

    def show_results(self):
        print("\nResults:") if self.correct_results else ''
        for product in self.correct_results:
            print(product['source'], product['name'], product['price'], product['info'], product['comment_count'])

        print("\nYou may want to look at these:") if self.near_results else ''
        for product in self.near_results:
            print(product['source'], product['name'], product['price'], product['info'], product['comment_count'])

        print("_________________________________\n")
