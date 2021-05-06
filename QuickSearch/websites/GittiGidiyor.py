import math
import re

from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class GittiGidiyor(SourceWebSite):
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
