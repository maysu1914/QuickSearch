import math
import re

from .SourceWebSite import SourceWebSite


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
        categories = {
            'All': 'tum--urunler',
            'Notebooks': 'laptop',
            'Smartphones': 'akilli-cep-telefonu',
            'Monitors': 'monitor',
            'Shoes': 'ayakkabi'
        }
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
