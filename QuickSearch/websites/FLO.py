from .SourceWebSite import SourceWebSite


class FLO(SourceWebSite):
    base_url = "https://www.flo.com.tr"
    source_name = 'FLO'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not content.find("div", "empty-information__heading"):
            if content.find("ul", "pagination justify-content-center"):
                page_number = int(content.find_all("li", "page-item")[-2].text)
                page_number = self.max_page if page_number > self.max_page else page_number
            else:
                page_number = 1

            if content.find("div", id="commerce-product-list"):
                self.results += self.get_products(content, url['search'])
            else:
                self.results += self.get_product(content, url['search'])

            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number)]
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
            'Shoes': '&category_id=770',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.flo.com.tr/search?q={}{}&sort=filter_price:asc'.format(search, category)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find("div", class_="row product-lists").find_all("div", "js-product-vertical"):
            product_brand = product.find("div", "product__brand").text.strip() if product.find("div",
                                                                                               "product__brand") else ''
            product_name = product_brand + ' ' + ' '.join(product.find("div", "product__name").text.split())
            if product.find("div", "product__prices-third") and ' TL' in product.find("div", "product__prices-third"):
                price_block = product.find("div", "product__prices-third")
                price_block.find("span").decompose()
                product_price = price_block.text.strip().split(',')[0].replace('.', '') + ' TL'
                if len(product_price) < 4:
                    print(price_block, product_price,product)
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
        # return []

        product_brand = content.find("div", "product__brand").text.strip() if content.find("div",
                                                                                           "product__brand") else ''
        product_name = product_brand + ' ' + ' '.join(content.find("h1", "product__name").text.split())
        if content.find("div", "product__prices-third"):
            price_block = content.find("div", "product__prices-third")
            price_block.find("span").decompose()
            product_price = price_block.text.strip().split(',')[0].replace('.', '') + ' TL'
            product_price_from = content.find("span", "product__prices-sale").text.strip().split(',')[0].replace(
                '.',
                '') + ' TL'
        elif content.find("span", "product__prices-sale"):
            product_price = content.find("span", "product__prices-sale").text.strip().split(',')[0].replace('.',
                                                                                                            '') + ' TL'
            if content.find("span", "product__prices-actual"):
                product_price_from = content.find("span", "product__prices-actual").text.strip().split(',')[
                                         0].replace('.',
                                                    '') + ' TL'
            else:
                product_price_from = ''
        else:
            return []

        if content.find("div", "product__badges"):
            for badge in content.find("div", "product__badges").find_all("div"):
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
