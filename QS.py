import itertools
import math
import re
from multiprocessing import Pool

import requests
from bs4 import BeautifulSoup as Soup
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

        return Soup(response.content, "lxml")

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


class MediaMarktTR(SourceWebSite):
    base_url = "https://www.mediamarkt.com.tr"
    source_name = 'MediaMarktTR'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and content.find("ul", "products-list"):
            page_number = int(
                content.find("ul", "pagination").find_all("li")[-2].text if content.find("ul", "pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            SourceWebSite.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number)]
                for page in page_list:
                    content = self.get_content(page)
                    SourceWebSite.results += self.get_products(content, url['search'])
            else:
                pass
        elif content and content.find("div", id="product-details"):
            SourceWebSite.results += self.get_product(content, url['search'])
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': 'query={search2}&searchProfile=onlineshop&channel=mmtrtr',
            'Notebooks': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DTa%25C5%259F%25C4%25B1nabilir%2BBilgisayarlar%25C2%25A7MediaTRtrc504926%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&page=&sourceRef=INVALID',
            'Smartphones': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DTelefon%25C2%25A7MediaTRtrc465595%26filterCategoriesROOT%252FTelefon%25C2%25A7MediaTRtrc465595%3DCep%2BTelefonlar%25C4%25B1%25C2%25A7MediaTRtrc504171%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&sourceRef=INVALID',
            'Monitors': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%26filterCategoriesROOT%252FBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%3DMonit%25C3%25B6r%25C2%25A7MediaTRtrc639581%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&sourceRef=INVALID',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        category = category.format(search1='%2B'.join(search.split()), search2='+'.join(search.split()))
        url = 'https://www.mediamarkt.com.tr/tr/search.html?{}'.format(category)
        return url

    def get_product(self, product, search):
        products = []

        product_name = product.find("h1", {'itemprop': 'name'}).text.strip()
        if product.find("meta", {'itemprop': 'price'}):
            product_price = product.find("meta", {'itemprop': 'price'})['content'] + ' TL'
        else:
            return products
        product_price_from = ''
        product_info = 'Ücretsiz Kargo' if product.find("span", {"data-layer": "deliveryinformation"}) else ''
        product_comment_count = product.find("div", "rating").findNext('span').text.strip() if product.find("div",
                                                                                                            "rating") else ''
        suitable_to_search = self.is_suitable_to_search(product_name, search)
        products.append(
            {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
             'old_price': product_price_from, 'info': product_info, 'comment_count': product_comment_count,
             'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)

        return products

    def get_products(self, content, search):
        products = []

        for product in content.find("ul", class_="products-list").find_all("li", recursive=False):
            if product.has_attr('class'):
                continue
            product_name = product.find("h2").text.strip()
            if product.find("div", class_='price small'):
                product_price = product.find("div", class_='price small').text.split(',')[0] + ' TL'
            else:
                continue
            product_price_from = product.find("div", class_='price price-xs price-old').text.split(',')[
                                     0] + ' TL' if product.find("div", class_='price price-xs price-old') else '1'
            product_info = ' '.join(
                product.find("span", {"data-layer": "deliveryinformation"}).parent.text.split()) if product.find("span",
                                                                                                                 {
                                                                                                                     "data-layer": "deliveryinformation"}) else ''
            product_comment_count = product.find("div", "rating").findNext('a').text.strip() if product.find("div",
                                                                                                             "rating") else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class GittiGidiyor(SourceWebSite):
    base_url = "https://www.gittigidiyor.com"
    source_name = 'GittiGidiyor'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not (content.find("div", "no-result-icon") or content.find("h2", "listing-similar-items")):
            page_number = math.ceil(int(re.findall('\d+', content.find("span", "result-count").text)[0]) / 48)
            page_number = self.max_page if page_number > self.max_page else page_number

            SourceWebSite.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sf=' + str(number) for number in range(2, page_number)]
                for page in page_list:
                    content = self.get_content(page)
                    SourceWebSite.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': 'arama/',
            'Notebooks': 'dizustu-laptop-notebook-bilgisayar',
            'Smartphones': 'cep-telefonu',
            'Monitors': 'cevre-birimleri/monitor',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.gittigidiyor.com/{}?k={}&sra=hpa'.format(category, search)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find("ul", class_="catalog-view clearfix products-container").find_all("li",
                                                                                                      recursive=False):
            product_name = ' '.join(product.find("h3", "product-title").text.split())
            if product.find("p", class_='fiyat robotobold price-txt'):
                product_price = product.find("p", class_='fiyat robotobold price-txt').text.split()[0].split(',')[
                                    0].replace('.', '') + ' TL'
                product_price_from = product.find("strike", class_='market-price-sel').text.split()[0].split(',')[
                                         0].replace('.', '') + ' TL'
            elif product.find("p", class_='fiyat price-txt robotobold price'):
                product_price = product.find("p", class_='fiyat price-txt robotobold price').text.split()[0].split(',')[
                                    0].replace('.', '') + ' TL'
                product_price_from = ''
            else:
                continue
            product_info = product.find("li", class_='shippingFree').text.strip() if product.find("li",
                                                                                                  class_='shippingFree') else ''
            if product.find("span", "gf-badge-position"):
                product_info += ' ' + product.find("span", "gf-badge-position").text
            else:
                pass
            product_comment_count = ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class Teknosa(SourceWebSite):
    base_url = "https://www.teknosa.com"
    source_name = 'Teknosa'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and self.is_result(url['search']) and not content.find("i", "icon-search-circle"):
            page_number = int(
                content.find("ul", "pagination").find_all("li")[-2].text if content.find("ul", "pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(1, page_number)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': ':relevance',
            'Notebooks': ':relevance:category:1020101',
            'Smartphones': ':relevance:category:100001',
            'Monitors': ':relevance:category:1020301',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.teknosa.com/arama/?q={}{}&sort=price-asc'.format(search, category)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find_all("div", "product-item"):
            product_name = product.find("div", "product-name").text.strip()
            if product.find("span", class_='price-tag new-price font-size-tertiary'):
                product_price = \
                    product.find("span", class_='price-tag new-price font-size-tertiary').text.split()[0].split(',')[
                        0].replace('.', '') + ' TL'
            else:
                continue
            product_price_from = product.find("span", class_='price-tag old-price block').text.split()[0].split(',')[
                                     0].replace('.', '') + ' TL' if product.find("span",
                                                                                 class_='price-tag old-price block') else ''
            product_info = 'KARGO BEDAVA' if int(product_price.split()[0]) > 100 else ''
            product_comment_count = ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products

    def is_result(self, search):
        url = "https://www.teknosa.com/arama/?s=" + search
        content = self.get_content(url)

        if content and not content.find("i", "icon-search-circle"):
            # print(1)
            return True
        else:
            # print(2)
            return False


class AmazonTR(SourceWebSite):
    base_url = "https://www.amazon.com.tr"
    source_name = 'AmazonTR'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and any("Şunu mu demek istediniz" in i.text for i in
                           content.select("span.a-size-medium.a-color-base.a-text-normal")):
            url['url'] = self.base_url + content.select("a.a-size-medium.a-link-normal.a-text-bold.a-text-italic")[0][
                'href']
            content = self.get_content(url['url'])
        else:
            pass

        if content and not (content.find("span", class_='a-size-medium a-color-base') or (content.find("h3",
                                                                                                       class_='a-size-base a-spacing-base a-color-base a-text-normal') and 'sonuç bulunamadı' in content.find(
            "h3", class_='a-size-base a-spacing-base a-color-base a-text-normal').text)):
            page_number = int(content.find("ul", "a-pagination").find_all("li")[-2].text if content.find("ul",
                                                                                                         "a-pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': '&i=computers&rh=n%3A12466439031%2Cn%3A12601898031',
            'Smartphones': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709907031',
            'Monitors': '&i=computers&rh=n%3A12466439031%2Cn%3A12601904031',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.amazon.com.tr/s?k={}{}&s=price-asc-rank'.format('+'.join(search.split()), category)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find_all("div", {"data-component-type": "s-search-result"}):
            if product.find("span", class_='a-size-medium a-color-base a-text-normal'):
                product_name = product.find("span", class_='a-size-medium a-color-base a-text-normal').text.strip()
            else:
                product_name = product.find("span", class_='a-size-base-plus a-color-base a-text-normal').text.strip()
            if product.find("span", "a-price-whole"):
                product_price = product.find("span", "a-price-whole").text.split()[0].replace(".", '').split(',')[
                                    0] + ' TL'
            else:
                continue
            product_price_from = \
                product.select("span.a-price.a-text-price")[0].text.replace("₺", '').replace(".", '').split(',')[
                    0] + ' TL' if len(product.select("span.a-price.a-text-price")) > 0 else ''
            product_info = ('Kargo BEDAVA' if 'BEDAVA' in product.select(
                ".a-row.a-size-base.a-color-secondary.s-align-children-center")[0].text else '') if len(
                product.select(".a-row.a-size-base.a-color-secondary.s-align-children-center")) > 0 else ''
            product_comment_count = \
                product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small span")[
                    -1].text.strip() if len(
                    product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small")) > 0 else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class Trendyol(SourceWebSite):
    base_url = "https://www.trendyol.com"
    source_name = 'Trendyol'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and content.find("div", "dscrptn") and "bulunamadı" not in content.find("div", "dscrptn").text:
            page_number = math.ceil(int(re.findall('\d+', content.find("div", "dscrptn").text)[0]) / 24)
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pi=' + str(number) for number in range(2, page_number + 1)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {'Notebooks': 'laptop', 'Smartphones': 'akilli-cep-telefonu', 'Monitors': 'monitor',
                      'All': 'tum--urunler'}
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.trendyol.com/{}?q={}&siralama=1'.format(category, search)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find_all("div", "p-card-wrppr"):
            product_brand = product.find("span", "prdct-desc-cntnr-ttl").text.strip() if product.find("span",
                                                                                                      "prdct-desc-cntnr-ttl") else ''
            product_name = product_brand + ' ' + product.find("span", "prdct-desc-cntnr-name").text.strip()
            if product.find("div", "prc-box-dscntd"):
                product_price = product.find("div", "prc-box-dscntd").text.split()[0].replace(".", '').split(',')[
                                    0] + ' TL'
            elif product.find("div", "prc-box-sllng"):
                product_price = product.find("div", "prc-box-sllng").text.split()[0].replace(".", '').split(',')[
                                    0] + ' TL'
            else:
                continue
            product_price_from = ''  # product.find("div","prc-box-orgnl").text.split()[0].replace(".",'').split(',')[0]+ ' TL' if product.find("div","prc-box-orgnl") is not None else ''
            product_info = product.find("div", "stmp").text.strip() if product.find("div", "stmp") is not None else ''
            product_comment_count = product.find("span", "ratingCount").text.strip() if product.find("span",
                                                                                                     "ratingCount") is not None else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class HepsiBurada(SourceWebSite):
    base_url = "https://www.hepsiburada.com"
    source_name = 'HepsiBurada'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not content.find("span", "product-suggestions-title"):
            page_number = int(content.select("#pagination > ul > li")[-1].text.strip() if content.select(
                "#pagination > ul > li") else 1)
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sayfa=' + str(number) for number in range(2, page_number + 1)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': '&filtreler=MainCategory.Id:98',
            'Smartphones': '&kategori=2147483642_371965',
            'Monitors': '&kategori=2147483646_3013120_57',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.hepsiburada.com/ara?q={}{}&siralama=artanfiyat'.format(search, category)
        return url

    def get_products(self, content, search):
        products = []
        for product in content.find_all("div", "product-detail"):
            if product.find("span", "out-of-stock-icon"):
                continue
            product_name = product.find("h3", "product-title").text.strip()
            if product.find("div", "price-value"):
                product_price = product.find("div", "price-value").text.replace(",", ".").replace('"', '').split()[
                                    0].replace(".", '')[:-2] + ' TL'
            elif product.find("span", "product-price"):
                product_price = product.find("span", "product-price").text.replace(",", ".").replace('"', '').split()[
                                    0].replace(".", '')[:-2] + ' TL'
            else:  # if product.find("span","can-pre-order-text"): ÖN SIPARIS
                continue
            product_price_from = product.find("del", "product-old-price").text.replace(",", ".").split()[0].replace(".",
                                                                                                                    '')[
                                 :-2] + ' TL' if product.find("del", "product-old-price") is not None else ''
            product_info = product.find("div", "shipping-status").text.strip() if product.find("div",
                                                                                               "shipping-status") is not None else ''
            product_comment_count = product.find("span", "number-of-reviews").text.strip() if product.find("span",
                                                                                                           "number-of-reviews") is not None else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class N11(SourceWebSite):
    base_url = "https://www.n11.com"
    source_name = 'n11'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not content.find("span", "result-mean-word") and not content.select(
                '#error404') and not content.select('#searchResultNotFound') and not content.select('.noResultHolder'):
            page_number = math.ceil(int(content.select(".resultText > strong")[0].text.replace(",", "")) / 28)
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pg=' + str(number) for number in range(2, page_number + 1)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': 'arama',
            'Notebooks': 'bilgisayar/dizustu-bilgisayar',
            'Smartphones': 'telefon-ve-aksesuarlari/cep-telefonu',
            'Monitors': 'bilgisayar/cevre-birimleri/monitor-ve-ekran',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.n11.com/{}?q={}&srt=PRICE_LOW'.format(category, '+'.join(search.split()))
        return url

    def get_products(self, content, search):
        products = []
        for product in content.find_all("div", "columnContent"):
            if product.find("h3", "productName"):
                product_name = product.find("h3", "productName").text.strip()
            else:
                continue
            product_price = product.find("a", "newPrice").text.replace(",", ".").replace('"', '').split()[0].replace(
                ".", '')[:-2] + ' TL'
            product_price_from = product.find("a", "oldPrice").text.replace(",", ".").split()[0].replace(".", '')[
                                 :-2] + ' TL' if product.find("a", "oldPrice") is not None else ''
            product_info = 'Ücretsiz Kargo' if product.find("span", "freeShipping") is not None else ''
            product_comment_count = product.find("span", "ratingText").text.strip() if product.find("span",
                                                                                                    "ratingText") is not None else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products


class VatanBilgisayar(SourceWebSite):
    base_url = "https://www.vatanbilgisayar.com"
    source_name = 'VatanBilgisayar'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not content.find("div", "empty-basket"):
            page_number = int(content.find("ul", "pagination").find_all("li")[-2].text.strip()) if len(
                content.find("ul", "pagination").find_all("li")) > 1 else 1
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                for page in page_list:
                    content = self.get_content(page)
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': '',
            'Notebooks': 'notebook/',
            'Smartphones': 'cep-telefonu-modelleri/',
            'Monitors': 'monitor/',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.vatanbilgisayar.com/arama/{}/{}?srt=UP'.format(search, category)
        return url

    def get_products(self, content, search):
        products = []
        for product in content.find_all("div", "product-list--list-page"):
            product_name = product.find("div", "product-list__product-name").text.strip()
            product_code = product.find("div", "product-list__product-code").text.strip()
            product_price = product.find("span", "product-list__price").text.strip().replace(".", '') + ' TL'
            product_price_from = product.find("span", "product-list__current-price").text.strip().replace(".",
                                                                                                          '') + ' TL'
            product_stock = product.find("span", "wrapper-condition__text").text.strip() if product.find("span",
                                                                                                         "wrapper-condition__text") else ''
            product_comment_count = product.find("a", "comment-count").text.strip()
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append({'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': product_code,
                             'price': product_price,
                             'old_price': product_price_from, 'info': product_stock,
                             'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_code,product_price,product_price_from,product_stock,product_comment_count)
        return products


class QuickSearch:
    max_page = 3

    def __init__(self, max_page=max_page):
        self.sources = [VatanBilgisayar, N11, HepsiBurada, Trendyol, AmazonTR, Teknosa, GittiGidiyor, MediaMarktTR]
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

        while not source_selections or any(
                int(source_selection) not in range(len(supported_sources) + 1) for source_selection in
                source_selections):
            source_selections = [source_selection.strip() for source_selection in input('Sources: ').split(',')]
            if '0' in source_selections:
                source_selections = range(1, len(supported_sources) + 1)

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


if __name__ == "__main__":
    while True:
        qs = QuickSearch(max_page=1)
        qs.search()
