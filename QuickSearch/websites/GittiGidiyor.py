import math
import re

from .SourceWebSite import SourceWebSite


class GittiGidiyor(SourceWebSite):
    base_url = "https://www.gittigidiyor.com"
    source_name = 'GittiGidiyor'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not (content.find("div", "no-result-icon") or content.find("h2", "listing-similar-items")):
            page_number = math.ceil(int(re.findall('\d+', content.find("span", "result-count").text)[0]) / 48)
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sf=' + str(number) for number in range(2, page_number)]
                contents = self.get_contents(page_list)
                for content in contents:
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        else:
            pass

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
