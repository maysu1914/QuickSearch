from .SourceWebSite import SourceWebSite


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
