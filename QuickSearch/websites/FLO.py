from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class FLO(SourceWebSite):
    base_url = "https://www.flo.com.tr"
    source_name = 'FLO'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("div", "empty-information__heading"):
            page_number = self.get_page_number(soup.find("ul", "pagination justify-content-center"))
            if soup.find("div", id="commerce-product-list"):
                results += self.get_products(content, url['search'])
            else:
                results += self.get_product(content, url['search'])

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
        if element:
            page_number = int(element.find_all("li")[-2].text)
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
            'Shoes': '&category_id=770',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.flo.com.tr/search?q={}{}&sort=filter_price:asc'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", "js-product-vertical"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.select("a:has(> .product__brand)"))
            data['price'] = self.get_product_price(product.find("div", "product__info"))
            data['old_price'] = self.get_product_old_price(product.find("div", "product__info"))
            data['info'] = self.get_product_info(product.select(".product__badges-item"))
            data['comment_count'] = None
            data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
            products.append(data)
        return products

    def get_product(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        data = {}
        data['source'] = '[{}]'.format(self.source_name)
        data['name'] = self.get_product_name(soup.select(".product"))
        data['price'] = self.get_product_price(soup.find("div", "product__info"))
        data['old_price'] = self.get_product_old_price(soup.find("div", "product__info"))
        data['info'] = self.get_product_info(soup.select(".product__badges-item"))
        data['comment_count'] = None
        data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
        return [data]

    def get_product_name(self, element):
        if element:
            product_name = list(element[0].select(".product__brand, .product__name"))
            return ' '.join(map(lambda i: i.text.strip(), product_name))
        else:
            return None

    def get_product_price(self, element):
        if element:
            price = element.find("div", "product__prices-third")
            if price:
                return int(self.get_text(price).split(',')[0].replace('.', ''))

            price = element.find("span", "product__prices-sale")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("div", "product__prices-third")
            if price:
                old_price = element.find("span", "product__prices-sale")
                return int(old_price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product__prices-sale")
            if price:
                old_price = element.find("span", "product__prices-actual")
                if old_price:
                    return int(old_price.text.split(',')[0].replace('.', ''))
            return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), element))
        else:
            return None
