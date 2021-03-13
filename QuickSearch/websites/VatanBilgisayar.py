from .SourceWebSite import SourceWebSite


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
            if product.find("span", "product-list__price"):
                product_price = product.find("span", "product-list__price").text.strip().replace(".", '') + ' TL'
            else:
                continue
            if product.find("span", "product-list__current-price"):
                product_price_from = product.find("span", "product-list__current-price").text.strip().replace(".",
                                                                                                              '') + ' TL'
            else:
                product_price_from = ''
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
