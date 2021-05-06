import math
import re

from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class Trendyol(SourceWebSite):
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
