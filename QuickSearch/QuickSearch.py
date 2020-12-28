from multiprocessing.pool import Pool

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
        self.sources = [VatanBilgisayar, N11, HepsiBurada, Trendyol, AmazonTR, Teknosa, GittiGidiyor, MediaMarktTR, FLO]
        self.categories = self.get_categories()
        self.max_page = max_page
        self.category_selection = None
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
                else:
                    pass
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

        for index in range(1, len(self.categories)):
            print(str(index) + '.', self.categories[index])

        while category_selection not in [str(num) for num in range(0, len(self.categories))]:
            category_selection = input('Category: ').strip()

        return self.categories[int(category_selection)]

    def get_source_input(self):
        source_selections = []
        supported_sources = []
        print("\nSelect the sources you want to search:")

        index = 1
        for source in self.sources:
            if self.category_selection in source.get_categories():
                supported_sources.append(source)
                print(str(index) + '.', source.source_name)
                index += 1
            else:
                pass

        while not source_selections or \
                any(
                    not source_selection.isnumeric() or int(source_selection) not in range(len(supported_sources) + 1)
                    for source_selection in source_selections
                ):
            source_selections = [source_selection.strip() for source_selection in
                                 input('Sources: ').split(',')]
            if '0' in source_selections:
                source_selections = [str(i) for i in range(1, len(supported_sources) + 1)]

        self.sources = supported_sources

        return source_selections

    @staticmethod
    def get_search_input():
        search_input = input('\nSearch Text: ').strip()
        return search_input

    def get_results(self):
        processes = []
        # print(os.cpu_count())
        with Pool() as pool:
            for source in self.source_selections:
                processes.append(
                    pool.apply_async(
                        self.sources[int(source) - 1](self.category_selection, max_page=self.max_page).search,
                        (self.search_text,)))
            for process in processes:
                self.raw_results += process.get()

        unique_results = []
        seen = set()
        for result in self.raw_results:
            t = tuple(result.items())
            if t not in seen:
                seen.add(t)
                unique_results.append(result)

        for i in sorted(unique_results, key=lambda i: [-i['suitable_to_search'], int(i['price'].split()[0])]):
            if i['suitable_to_search']:
                self.correct_results.append(i)
            else:
                t = i.copy()
                t['suitable_to_search'] = True
                t = tuple(t.items())
                if t not in seen:
                    self.near_results.append(i)
                else:
                    # print(i)
                    pass

    def show_results(self):
        print("\nResults:") if self.correct_results else ''
        for product in self.correct_results:
            print(product['source'], product['name'], product['price'], product['info'], product['comment_count'])

        print("\nYou may want to look at these:") if self.near_results else ''
        for product in self.near_results:
            print(product['source'], product['name'], product['price'], product['info'], product['comment_count'])

        print("_________________________________\n")
