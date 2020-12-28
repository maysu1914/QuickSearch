import itertools
import re
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri


class SourceWebSite:
    max_page = 5
    results = []

    def __init__(self, category, max_page=max_page):
        self.category = category
        self.max_page = max_page

    def search(self, search):
        urls = self.get_url(search)
        for url in urls:
            self.get_results(url)
        return self.results

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

    @staticmethod
    def find_nth(haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start + len(needle))
            n -= 1
        return start

    @staticmethod
    def get_content(url):
        print(url)
        count = 3
        verify = True
        while count > 0:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                }
                response = requests.get(url, timeout=10, headers=headers, verify=verify)
                # print(response.url)
                # print(response.content)
                count = 0
            except requests.exceptions.SSLError as e:
                print(url, "SSL error!")
                print("Trying without SSL verify...", count)
                verify = False
                count -= 1
                if count == 0:
                    return None
            except Exception as e:
                print(url, e)
                print("Trying...", count)
                count -= 1
                if count == 0:
                    return None

        return BeautifulSoup(response.content, "lxml")

    @staticmethod
    def get_contents(url_list):
        contents = []
        threads = [ThreadPoolExecutor().submit(SourceWebSite.get_content, url) for url in url_list]
        for thread in threads:
            contents.append(thread.result())
        return contents

    @staticmethod
    def is_suitable_to_search(product_name, search):
        product_name = product_name.lower()
        search = search.lower()

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

    @abstractmethod
    def get_categories(self):
        pass

    @abstractmethod
    def create_url(self, search, param):
        pass

    @abstractmethod
    def get_results(self, url):
        pass
