import itertools
import re
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri


class SourceWebSite:
    max_page = 5

    def __init__(self, category, max_page=max_page):
        self.category = category
        self.max_page = max_page
        self.executor = ThreadPoolExecutor()

    def search(self, search):
        results = []
        urls = self.get_url(search)  # multiple results if search has list
        threads = [self.executor.submit(self.get_results, url) for url in urls]
        for thread in threads:
            results += thread.result()
        return results

    def is_product_list_page(self, element):
        pass

    def is_did_you_mean(self, element):
        pass

    def get_url(self, search):
        categories = self.get_categories()

        if '[' in search and ']' in search:
            if self.category in categories:
                urls = []
                static = search
                dynamic = []

                for a, b in zip(range(1, search.count('[') + 1), range(1, search.count(']') + 1)):
                    start = self.find_nth(search, '[', a)
                    end = self.find_nth(search, ']', a) + 1
                    part = search[start:end]
                    dynamic.append(part.strip('][').split(','))
                    static = static.replace(part, '')

                for i in list(itertools.product(*dynamic)):
                    search = (' '.join(static.split()) + ' ' + ' '.join(i)).strip()
                    url = self.create_url(search, categories[self.category])
                    urls.append({'search': search, 'url': requote_uri(url)})
                # print(url)
                return urls
            else:
                return []
        else:
            if self.category in categories:
                url = self.create_url(search, categories[self.category])
                # print(url)
                return [{'search': search, 'url': requote_uri(url)}]
            else:
                return []

    def get_page_content(self, url, counter=3):
        """
        Content retriever
        :param url: the link whose content is to be returned
        :param counter: how many times of retrying
        :return: content of response
        """
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
        for count in range(1, counter + 1):
            try:
                response = requests.get(url, timeout=10, headers=headers)
                return response.content
            except Exception as e:
                print('Error occurred while getting page content!', count, url, e)
                continue
        return None

    def get_contents(self, url_list):
        contents = []
        threads = [ThreadPoolExecutor().submit(self.get_page_content, url) for url in url_list]
        for thread in threads:
            contents.append(thread.result())
        return contents

    @staticmethod
    def get_categories():
        pass

    @staticmethod
    def create_url(search, param):
        pass

    def get_results(self, url):
        pass

    def get_products(self, content, search):
        pass

    def get_page_number(self, element):
        pass

    @staticmethod
    def is_suitable_to_search(product_name, search):
        if product_name:
            product_name = product_name.lower()
            search = search.lower()
        else:
            return False

        search_numbers = re.findall('\d+', search)
        search_words = search.lower()

        for number in search_numbers:
            search_words = search_words.replace(number, '')

        search_words = [word if len(word) > 2 else None for word in search_words.split()]

        search_words = [i for i in search_words if i]

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
    def find_nth(haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start + len(needle))
            n -= 1
        return start

    def get_text(self, element):
        """
        it will parse the text of element without children's
        :param element:
        :return: string
        """
        return ''.join(element.find_all(text=True, recursive=False)).strip()

    def get_product_name(self, element):
        pass

    def get_product_code(self, element):
        pass

    def get_product_price(self, element):
        pass

    def get_product_old_price(self, element):
        pass

    def get_product_info(self, element):
        pass

    def get_product_comment_count(self, element):
        pass
