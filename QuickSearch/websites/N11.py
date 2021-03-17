import math

from .SourceWebSite import SourceWebSite


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
