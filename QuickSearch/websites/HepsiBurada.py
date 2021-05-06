from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class HepsiBurada(SourceWebSite):
    base_url = "https://www.hepsiburada.com"
    source_name = 'HepsiBurada'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("span", "product-suggestions-title"):
            page_number = self.get_page_number(soup.select("#pagination > ul > li"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sayfa=' + str(number) for number in range(2, page_number + 1)]
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
            page_number = int(element[-1].text.strip())
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
        soup = BeautifulSoup(content, "lxml")
        products = []
        for product in soup.select("div.box.product"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h3", "product-title"))
            data['price'] = self.get_product_price(product.find("div", "product-detail"))
            data['old_price'] = self.get_product_old_price(product.find("div", "product-detail"))
            data['info'] = self.get_product_info(product.select("div.shipping-status, .dod-badge"))
            data['comment_count'] = self.get_product_comment_count(product.find("span", "number-of-reviews"))
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
            price = element.find("div", "price-value")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product-price")
            if price:
                return int(price.text.split(',')[0].replace('.', ''))
            return None

    def get_product_old_price(self, element):
        if element:
            price = element.find("div", "price-value")
            if price:
                old_price = element.find("span", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))

                old_price = element.find("del", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))

            price = element.find("span", "product-price")
            if price:
                old_price = element.find("del", "product-old-price")
                if old_price:
                    return int(price.text.split(',')[0].replace('.', ''))
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
