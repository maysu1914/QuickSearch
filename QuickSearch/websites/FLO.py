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

        for product in soup.find("div", class_="row product-lists").find_all("div", "js-product-vertical"):
            product_brand = product.find("div", "product__brand").text.strip() if product.find("div",
                                                                                               "product__brand") else ''
            product_name = product_brand + ' ' + ' '.join(product.find("div", "product__name").text.split())
            if product.find("div", "product__prices-third") and ' TL' in product.find("div", "product__prices-third"):
                price_block = product.find("div", "product__prices-third")
                price_block.find("span").decompose()
                product_price = price_block.text.strip().split(',')[0].replace('.', '') + ' TL'
                if len(product_price) < 4:
                    print(price_block, product_price, product)
                product_price_from = product.find("span", "product__prices-sale").text.strip().split(',')[0].replace(
                    '.',
                    '') + ' TL'
            elif product.find("span", "product__prices-sale"):
                product_price = product.find("span", "product__prices-sale").text.strip().split(',')[0].replace('.',
                                                                                                                '') + ' TL'
                if product.find("span", "product__prices-actual"):
                    product_price_from = product.find("span", "product__prices-actual").text.strip().split(',')[
                                             0].replace('.',
                                                        '') + ' TL'
                else:
                    product_price_from = ''
            else:
                continue

            if product.find("div", "product__badges"):
                for badge in product.find("div", "product__badges").find_all("div"):
                    product_name += ' ' + badge.text
            else:
                pass
            product_info = ''

            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': '', 'suitable_to_search': suitable_to_search})
        return products

    def get_product(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        # return []

        product_brand = soup.find("div", "product__brand").text.strip() if soup.find("div",
                                                                                     "product__brand") else ''
        product_name = product_brand + ' ' + ' '.join(soup.find("h1", "product__name").text.split())
        if soup.find("div", "product__prices-third"):
            price_block = soup.find("div", "product__prices-third")
            price_block.find("span").decompose()
            product_price = price_block.text.strip().split(',')[0].replace('.', '') + ' TL'
            product_price_from = soup.find("span", "product__prices-sale").text.strip().split(',')[0].replace(
                '.',
                '') + ' TL'
        elif soup.find("span", "product__prices-sale"):
            product_price = soup.find("span", "product__prices-sale").text.strip().split(',')[0].replace('.',
                                                                                                         '') + ' TL'
            if soup.find("span", "product__prices-actual"):
                product_price_from = soup.find("span", "product__prices-actual").text.strip().split(',')[
                                         0].replace('.',
                                                    '') + ' TL'
            else:
                product_price_from = ''
        else:
            return []

        if soup.find("div", "product__badges"):
            for badge in soup.find("div", "product__badges").find_all("div"):
                product_name += ' ' + badge.text
        else:
            pass
        product_info = ''

        suitable_to_search = self.is_suitable_to_search(product_name, search)
        product = {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None,
                   'price': product_price,
                   'old_price': product_price_from, 'info': product_info,
                   'comment_count': '', 'suitable_to_search': suitable_to_search}
        # print(product_name,product_price,product_info,product_comment_count)
        return [product]
