from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class Teknosa(SourceWebSite):
    base_url = "https://www.teknosa.com"
    source_name = 'Teknosa'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and not soup.find("i", "icon-search-circle"):
            page_number = self.get_page_number(soup.find("ul", "pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(1, page_number)]
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
            'All': ':relevance',
            'Notebooks': ':relevance:category:1020101',
            'Desktop PCs': ':relevance:category:10201',
            'Smartphones': ':relevance:category:100001',
            'Monitors': ':relevance:category:1020301',
            'Digital Cameras': ':relevance:category:10701',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.teknosa.com/arama/?q={}{}&sort=price-asc'.format(search, category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", "product-item"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("div", "product-name"))
            data['price'] = self.get_product_price(product.find("span", "new-price"))
            data['old_price'] = self.get_product_old_price(product.find("span", "old-price"))
            data['info'] = self.get_product_info(product.select("div.product-list-badge-item, div.only-in-store-badge"))
            data['comment_count'] = None
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
            return int(element.text.split()[0].split(',')[0].replace('.', ''))
        else:
            return None

    def get_product_info(self, element):
        if element:
            return ' '.join(map(lambda i: i.text.strip(), list(element)))
        else:
            return None
