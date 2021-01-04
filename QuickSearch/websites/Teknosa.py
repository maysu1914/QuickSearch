from .SourceWebSite import SourceWebSite


class Teknosa(SourceWebSite):
    base_url = "https://www.teknosa.com"
    source_name = 'Teknosa'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and not content.find("i", "icon-search-circle"):
            page_number = int(
                content.find("ul", "pagination").find_all("li")[-2].text if content.find("ul", "pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(1, page_number)]
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
            'All': ':relevance',
            'Notebooks': ':relevance:category:1020101',
            'Smartphones': ':relevance:category:100001',
            'Monitors': ':relevance:category:1020301',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.teknosa.com/arama/?q={}{}&sort=price-asc'.format(search, category)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find_all("div", "product-item"):
            product_name = product.find("div", "product-name").text.strip()
            if product.find("span", class_='price-tag new-price font-size-tertiary'):
                product_price = \
                    product.find("span", class_='price-tag new-price font-size-tertiary').text.split()[0].split(',')[
                        0].replace('.', '') + ' TL'
            else:
                continue
            product_price_from = product.find("span", class_='price-tag old-price block').text.split()[0].split(',')[
                                     0].replace('.', '') + ' TL' if product.find("span",
                                                                                 class_='price-tag old-price block') else ''
            product_info = 'KARGO BEDAVA' if int(product_price.split()[0]) > 100 else ''
            product_comment_count = ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products

    # Teknos's website was showing the wrong products if no result when filtered search only, it seems they fixed it
    # def get_result(self, url):
    #     urls = ["https://www.teknosa.com/arama/?s=" + url['search'], url['url']]
    #     contents = self.get_contents(urls)
    #
    #     if contents[0] and not contents[0].find("i", "icon-search-circle"):
    #         # print(1)
    #         return contents[1]
    #     else:
    #         # print(2)
    #         return False
