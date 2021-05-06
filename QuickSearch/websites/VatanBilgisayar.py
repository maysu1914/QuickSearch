from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class VatanBilgisayar(SourceWebSite):
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
