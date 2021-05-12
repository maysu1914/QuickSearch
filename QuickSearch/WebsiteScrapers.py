import concurrent
import itertools
import math
import re
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.exceptions import SSLError
from requests.utils import requote_uri


class WebsiteScraper:

    def __init__(self, category, max_page=5):
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
    def create_url(search, param):
        pass

    @staticmethod
    def get_page_content(url, counter=3, dynamic_verification=True):
        """
        Content retriever
        :param dynamic_verification: try without SSL verify if needed
        :param url: the link whose content is to be returned
        :param counter: how many times of retrying
        :return: content of response
        """
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
        verify = True
        for count in range(1, counter + 1):
            try:
                response = requests.get(url, timeout=10, headers=headers, verify=verify)
                return response.content
            except Exception as e:
                print('Error occurred while getting page content!', count, url, e)
                if dynamic_verification and type(e) == SSLError:
                    verify = False
                continue
        return ''

    def is_did_you_mean(self, element):
        pass

    def is_product_list_page(self, element):
        pass

    def get_contents(self, url_list):
        threads = [ThreadPoolExecutor().submit(self.get_page_content, url) for url in url_list]
        for thread in concurrent.futures.as_completed(threads):
            yield thread.result()

    def get_results(self, url):
        pass

    def get_page_number(self, element):
        pass

    def get_products(self, content, search):
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

    @staticmethod
    def get_text(element):
        """
        it will parse the text of element without children's
        :param element:
        :return: string
        """
        return ''.join(element.find_all(text=True, recursive=False)).strip()

    def get_product_name(self, element):
        pass

    def get_product_price(self, element):
        pass

    def get_product_old_price(self, element):
        pass

    def get_product_info(self, element):
        pass

    def get_product_comment_count(self, element):
        pass

    @staticmethod
    def get_categories():
        pass


class VatanbilgisayarScraper(WebsiteScraper):
    base_url = "https://www.vatanbilgisayar.com"
    source_name = 'VatanBilgisayar'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("div", "empty-basket"):
            page_number = self.get_page_number(soup.find("ul", "pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, element):
        if element and len(element.find_all("li")) > 1:
            page_number = int(element.find_all("li")[-2].text.strip())
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': 'notebook/',
            'Desktop PCs': 'masaustu-bilgisayarlar/',
            'Smartphones': 'cep-telefonu-modelleri/',
            'Monitors': 'monitor/',
            'Digital Cameras': 'fotograf-makinesi/',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.vatanbilgisayar.com/arama/{}/{}?srt=UP'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []
        for product in soup.find_all("div", "product-list--list-page"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("div", "product-list__product-name"))
            data['price'] = self.get_product_price(product.find("span", "product-list__price"))
            data['old_price'] = self.get_product_old_price(product.find("span", "product-list__current-price"))
            data['info'] = self.get_product_info(product.select("span.wrapper-condition__text"))
            data['comment_count'] = self.get_product_comment_count(product.find("a", "comment-count"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            return int(element.text.split()[0].split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            if element.text.strip():
                return int(element.text.split()[0].split(',')[0].replace('.', ''))
            else:
                return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), list(element)))
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element.text.strip()
        else:
            return None


class N11Scraper(WebsiteScraper):
    base_url = "https://www.n11.com"
    source_name = 'n11'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and self.is_product_list_page(soup):
            page_number = self.get_page_number(soup.select(".resultText > strong"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pg=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def is_product_list_page(self, page):
        did_you_mean = page.find("span", "result-mean-word")
        error = page.select('#error404')
        not_found = page.select('#searchResultNotFound')
        no_result = page.select('.noResultHolder')
        if did_you_mean or error or not_found or no_result:
            return False
        else:
            return True

    def get_page_number(self, element):
        if element:
            page_number = math.ceil(int(element[0].text.replace(",", "")) / 28)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': 'arama',
            'Notebooks': 'bilgisayar/dizustu-bilgisayar',
            'Desktop PCs': 'bilgisayar/masaustu-bilgisayar',
            'Smartphones': 'telefon-ve-aksesuarlari/cep-telefonu',
            'Monitors': 'bilgisayar/cevre-birimleri/monitor-ve-ekran',
            'Digital Cameras': 'fotograf-ve-kamera/fotograf-makinesi',
            'Shoes': 'ayakkabi-ve-canta',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.n11.com/{}?q={}&srt=PRICE_LOW'.format(category, '+'.join(search.split()))
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []
        for product in soup.select("#view > ul > li"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h3", "productName"))
            data['price'] = self.get_product_price(product.find("a", "newPrice"))
            data['old_price'] = self.get_product_old_price(product.find("a", "oldPrice"))
            data['info'] = self.get_product_info(product.find("span", "freeShipping"))
            data['comment_count'] = self.get_product_comment_count(product.find("span", "ratingText"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            return int(element.text.split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            return int(element.text.split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_info(self, element):
        if element:
            return 'Ücretsiz Kargo'
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element.text.strip()
        else:
            return None


class HepsiburadaScraper(WebsiteScraper):
    base_url = "https://www.hepsiburada.com"
    source_name = 'HepsiBurada'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("span", "product-suggestions-title"):
            page_number = self.get_page_number(soup.select("#pagination > ul > li"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sayfa=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, element):
        if element:
            page_number = int(element[-1].text.strip())
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': '&kategori=2147483646_3000500_98',
            'Desktop PCs': '&kategori=2147483646_3000500_34',
            'Smartphones': '&kategori=2147483642_371965',
            'Monitors': '&kategori=2147483646_3013120_57',
            'Digital Cameras': '&kategori=2147483606_60002083',
            'Shoes': '&kategori=2147483636',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.hepsiburada.com/ara?q={}{}&siralama=artanfiyat'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []
        for product in soup.select("div.box.product"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h3", "product-title"))
            data['price'] = self.get_product_price(product.find("div", "product-detail"))
            data['old_price'] = self.get_product_old_price(product.find("div", "product-detail"))
            data['info'] = self.get_product_info(product.select("div.shipping-status, .dod-badge"))
            data['comment_count'] = self.get_product_comment_count(product.find("span", "number-of-reviews"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.find("div", "price-value")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product-price")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("div", "price-value")
            if price:
                old_price = element.find("span", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))

                old_price = element.find("del", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product-price")
            if price:
                old_price = element.find("del", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), list(element)))
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element.text.strip()
        else:
            return None


class TrendyolScraper(WebsiteScraper):
    base_url = "https://www.trendyol.com"
    source_name = 'Trendyol'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and self.is_product_list_page(soup.find("div", "dscrptn")):
            page_number = self.get_page_number(soup.find("div", "dscrptn"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pi=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def is_product_list_page(self, element):
        if element:
            if "bulunamadı" not in element.text:
                return True
            else:
                return False
        else:
            return False

    def get_page_number(self, element):
        if element:
            page_number = math.ceil(int(re.findall('\d+', element.text)[0]) / 24)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': 'tum--urunler',
            'Notebooks': 'laptop',
            'Desktop PCs': 'masaustu-bilgisayar',
            'Smartphones': 'akilli-cep-telefonu',
            'Monitors': 'monitor',
            'Digital Cameras': 'dijital-fotograf-makineleri',
            'Shoes': 'ayakkabi'
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.trendyol.com/{}?q={}&siralama=1'.format(category, search)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", "p-card-wrppr"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("div", "prdct-desc-cntnr-ttl-w"))
            data['price'] = self.get_product_price(product.find("div", "prdct-desc-cntnr-wrppr"))
            data['old_price'] = self.get_product_old_price(product.find("div", "prdct-desc-cntnr-wrppr"))
            data['info'] = self.get_product_info(product.select("div.stmp.fc"))
            data['comment_count'] = self.get_product_comment_count(product.find("span", "ratingCount"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            product_name = list(element.select(".prdct-desc-cntnr-ttl, .prdct-desc-cntnr-name"))
            return ' '.join(map(lambda i: i.text.strip(), product_name))
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.find("div", "prc-box-dscntd")
            if price:
                return int(price.text.split()[0].split(',')[0].replace('.', ''))

            price = element.find("div", "prc-box-sllng")
            if price:
                return int(price.text.split()[0].split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("div", "prc-box-dscntd")
            if price:
                old_price = element.find("div", "prc-box-sllng")
                return int(old_price.text.split()[0].split(',')[0].replace('.', ''))

            price = element.find("div", "prc-box-sllng")
            if price:
                old_price = element.find("div", "prc-box-orgnl")
                if old_price:
                    return int(old_price.text.split()[0].split(',')[0].replace('.', ''))
                return None
            return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), list(element)))
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element.text.strip()
        else:
            return None


class AmazonScraper(WebsiteScraper):
    base_url = "https://www.amazon.com.tr"
    source_name = 'AmazonTR'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and self.is_did_you_mean(soup.select("span.a-size-medium.a-color-base.a-text-normal")):
            pathname = soup.select("a.a-size-medium.a-link-normal.a-text-bold.a-text-italic")[0]['href']
            url['url'] = urljoin(self.base_url, pathname)
            content = self.get_page_content(url['url'])
            soup = BeautifulSoup(content, "lxml")
        else:
            pass

        if soup and self.is_product_list_page(soup):
            page_number = self.get_page_number(soup.find("ul", "a-pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def is_product_list_page(self, page):
        no_results_all = page.find("span", class_='a-size-medium a-color-base')
        no_results_category = page.find("h3", class_='a-size-base a-spacing-base a-color-base a-text-normal')
        if no_results_all:
            return False
        elif no_results_category and 'sonuç bulunamadı' in no_results_category.text:
            return False
        else:
            return True

    def is_did_you_mean(self, element):
        return any("Şunu mu demek istediniz" in i.text for i in element)

    def get_page_number(self, element):
        if element:
            page_number = int(element.find_all("li")[-2].text)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': '&i=computers&rh=n%3A12466439031%2Cn%3A12601898031',
            'Desktop PCs': '&i=computers&rh=n%3A12601903031',
            'Smartphones': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709907031',
            'Monitors': '&i=computers&rh=n%3A12466439031%2Cn%3A12601904031',
            'Digital Cameras': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709883031%2Cn%3A13709933031',
            'Shoes': '&i=fashion&rh=n%3A12466553031',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.amazon.com.tr/s?k={}{}&s=price-asc-rank'.format('+'.join(search.split()), category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", {"data-component-type": "s-search-result"}):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("a", class_='a-link-normal a-text-normal'))
            data['price'] = self.get_product_price(product.find("span", "a-price-whole"))
            data['old_price'] = self.get_product_old_price(product.select("span.a-price.a-text-price"))
            data['info'] = self.get_product_info(product.select(".a-row.a-size-base.a-color-secondary"))
            data['comment_count'] = self.get_product_comment_count(product.select(".a-spacing-top-micro .a-size-small"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.text.split(',')[0].replace('.', '')
            return int(price)
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            if len(element) > 0:
                old_price = element[0].text.strip()[0].replace('.', '')
                return int(old_price)
            else:
                return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            if 'BEDAVA' in element[0].text:
                return 'Kargo BEDAVA'
            else:
                return None
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            comment_count = element[0].text.split()[-1]
            if comment_count.isdigit():
                return comment_count
            else:
                return None
        else:
            return None


class TeknosaScraper(WebsiteScraper):
    base_url = "https://www.teknosa.com"
    source_name = 'Teknosa'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("i", "icon-search-circle"):
            page_number = self.get_page_number(soup.find("ul", "pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(1, page_number)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, element):
        if element:
            page_number = int(element.find_all("li")[-2].text)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': ':relevance',
            'Notebooks': ':relevance:category:1020101',
            'Desktop PCs': ':relevance:category:10201',
            'Smartphones': ':relevance:category:100001',
            'Monitors': ':relevance:category:1020301',
            'Digital Cameras': ':relevance:category:10701',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.teknosa.com/arama/?q={}{}&sort=price-asc'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", "product-item"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("div", "product-name"))
            data['price'] = self.get_product_price(product.find("span", "new-price"))
            data['old_price'] = self.get_product_old_price(product.find("span", "old-price"))
            data['info'] = self.get_product_info(product.select("div.product-list-badge-item, div.only-in-store-badge"))
            data['comment_count'] = None
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            return int(element.text.split()[0].split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            return int(element.text.split()[0].split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), list(element)))
        else:
            return None


class GittigidiyorScraper(WebsiteScraper):
    base_url = "https://www.gittigidiyor.com"
    source_name = 'GittiGidiyor'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and self.is_product_list_page(soup):
            page_number = self.get_page_number(soup.find("span", "result-count"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sf=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, element):
        if element:
            page_number = math.ceil(int(re.findall('\d+', element.text)[0]) / 48)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    def is_product_list_page(self, page):
        no_result_icon = page.find("div", "no-result-icon")
        similar_items = page.find("h2", "listing-similar-items")
        search_container = page.find(id='SearchCon')
        if no_result_icon or similar_items or search_container:
            return False
        else:
            return True

    @staticmethod
    def get_categories():
        categories = {
            'All': 'arama/',
            'Notebooks': 'dizustu-laptop-notebook-bilgisayar',
            'Desktop PCs': 'masaustu-desktop-bilgisayar',
            'Smartphones': 'cep-telefonu',
            'Monitors': 'cevre-birimleri/monitor',
            'Digital Cameras': 'dijital-fotograf-makinesi',
            'Shoes': 'ayakkabi',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.gittigidiyor.com/{}?k={}&sra=hpa'.format(category, search)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("li", "srp-item-list"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h3", "product-title"))
            data['price'] = self.get_product_price(product.find("div", "product-price"))
            data['old_price'] = self.get_product_old_price(product.find("div", "product-price"))
            data['info'] = self.get_product_info(product.select("li.shippingFree, [class*='-badge-position']"))
            data['comment_count'] = None
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return ' '.join(element.text.split())
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.find("p", "extra-price")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))

            price = element.find("p", "fiyat")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("p", "extra-price")
            if price:
                old_price = element.find("p", "fiyat")
                if old_price:
                    return int(old_price.text.split(',')[0].replace('.', ''))

                old_price = element.find("div", "discount-detail-grey")
                if old_price:
                    return int(old_price.text.split(',')[0].replace('.', ''))

            price = element.find("p", "fiyat")
            if price:
                old_price = element.find("div", "discount-detail-grey")
                if old_price:
                    return int(old_price.text.split(',')[0].replace('.', ''))
                else:
                    return None
            return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: self.get_text(i), list(element)))
        else:
            return None


class MediamarktScraper(WebsiteScraper):
    base_url = "https://www.mediamarkt.com.tr"
    source_name = 'MediaMarktTR'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and soup.find("ul", "products-list"):
            page_number = self.get_page_number(soup.find("ul", "pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        elif soup and soup.find("div", id="product-details"):
            results += self.get_product(content, url['search'])
        else:
            pass
        return results

    def get_page_number(self, element):
        if element:
            page_number = int(element.find_all("li")[-2].text)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': 'query={search2}&searchProfile=onlineshop&channel=mmtrtr',
            'Notebooks': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DTa%25C5%259F%25C4%25B1nabilir%2BBilgisayarlar%25C2%25A7MediaTRtrc504926%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Desktop PCs': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DMasa%25C3%25BCst%25C3%25BC%2BBilgisayarlar%25C2%25A7MediaTRtrc504957%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Smartphones': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DTelefon%25C2%25A7MediaTRtrc465595%26filterCategoriesROOT%252FTelefon%25C2%25A7MediaTRtrc465595%3DCep%2BTelefonlar%25C4%25B1%25C2%25A7MediaTRtrc504171%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Monitors': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%26filterCategoriesROOT%252FBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%3DMonit%25C3%25B6r%25C2%25A7MediaTRtrc639581%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Digital Cameras': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DFoto%2B%2526%2BKamera%25C2%25A7MediaTRtrc465682%26filterCategoriesROOT%252FFoto%2B%2526%2BKamera%25C2%25A7MediaTRtrc465682%3DFoto%25C4%259Fraf%2BMakineleri%25C2%25A7MediaTRtrc465683%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        category = category.format(search1='%2B'.join(search.split()), search2='+'.join(search.split()))
        url = 'https://www.mediamarkt.com.tr/tr/search.html?{}&sort=price&sourceRef=INVALID'.format(category)
        return url

    def get_product(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        data = {}
        data['source'] = '[{}]'.format(self.source_name)
        data['name'] = self.get_product_name(soup.find("h1", {'itemprop': 'name'}))
        data['price'] = self.get_product_price(soup.select("div.price.big"))
        data['old_price'] = None
        data['info'] = self.get_product_info(soup.select("div.price-details > small"))
        data['comment_count'] = self.get_product_comment_count(soup.select("dd.product-rate > span.clickable > span"))
        data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
        return [data]

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.select("ul.products-list > li:not([class])"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h2"))
            data['price'] = self.get_product_price(product.select("div.price.small"))
            data['old_price'] = self.get_product_old_price(product.select("div.price.price-old"))
            data['info'] = self.get_product_info(product.select("div.price-box > small"))
            data['comment_count'] = self.get_product_comment_count(product.select("span.see-reviews"))
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product_name(self, element):
        if element:
            return element.text.strip()
        else:
            return None

    def get_product_price(self, element):
        if element:
            return int(element[0].text.split(',')[0])
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            return int(element[0].text.split(',')[0])
        else:
            return None

    def get_product_info(self, element):
        if element:
            if element[0].find("img"):
                return 'Ücretsiz Kargo'
            else:
                return element[0].text.strip()
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element[0].text.strip()
        else:
            return None


class FloScraper(WebsiteScraper):
    base_url = "https://www.flo.com.tr"
    source_name = 'FLO'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("div", "empty-information__heading"):
            page_number = self.get_page_number(soup.find("ul", "pagination justify-content-center"))
            if soup.find("div", id="commerce-product-list"):
                results += self.get_products(content, url['search'])
            else:
                results += self.get_product(content, url['search'])

            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass
        return results

    def get_page_number(self, element):
        if element:
            page_number = int(element.find_all("li")[-2].text)
            if page_number > self.max_page:
                return self.max_page
            else:
                return page_number
        else:
            return 1

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Shoes': '&category_id=770',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.flo.com.tr/search?q={}{}&sort=filter_price:asc'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", "js-product-vertical"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.select("a:has(> .product__brand)"))
            data['price'] = self.get_product_price(product.find("div", "product__info"))
            data['old_price'] = self.get_product_old_price(product.find("div", "product__info"))
            data['info'] = self.get_product_info(product.select(".product__badges-item"))
            data['comment_count'] = None
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        data = {}
        data['source'] = '[{}]'.format(self.source_name)
        data['name'] = self.get_product_name(soup.select(".product"))
        data['price'] = self.get_product_price(soup.find("div", "product__info"))
        data['old_price'] = self.get_product_old_price(soup.find("div", "product__info"))
        data['info'] = self.get_product_info(soup.select(".product__badges-item"))
        data['comment_count'] = None
        data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
        return [data]

    def get_product_name(self, element):
        if element:
            product_name = list(element[0].select(".product__brand, .product__name"))
            return ' '.join(map(lambda i: i.text.strip(), product_name))
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.find("div", "product__prices-third")
            if price:
                return int(self.get_text(price).split(',')[0].replace('.', ''))

            price = element.find("span", "product__prices-sale")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("div", "product__prices-third")
            if price:
                old_price = element.find("span", "product__prices-sale")
                return int(old_price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product__prices-sale")
            if price:
                old_price = element.find("span", "product__prices-actual")
                if old_price:
                    return int(old_price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), element))
        else:
            return None
