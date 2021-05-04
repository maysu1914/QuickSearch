import math

from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class N11(SourceWebSite):
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
        for product in soup.find_all("div", "columnContent"):
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
