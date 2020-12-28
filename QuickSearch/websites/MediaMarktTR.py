from .SourceWebSite import SourceWebSite


class MediaMarktTR(SourceWebSite):
    base_url = "https://www.mediamarkt.com.tr"
    source_name = 'MediaMarktTR'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and content.find("ul", "products-list"):
            page_number = int(
                content.find("ul", "pagination").find_all("li")[-2].text if content.find("ul", "pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number)]
                contents = self.get_contents(page_list)
                for content in contents:
                    self.results += self.get_products(content, url['search'])
            else:
                pass
        elif content and content.find("div", id="product-details"):
            self.results += self.get_product(content, url['search'])
        else:
            pass

    @staticmethod
    def get_categories():
        categories = {
            'All': 'query={search2}&searchProfile=onlineshop&channel=mmtrtr',
            'Notebooks': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DTa%25C5%259F%25C4%25B1nabilir%2BBilgisayarlar%25C2%25A7MediaTRtrc504926%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&page=&sourceRef=INVALID',
            'Smartphones': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DTelefon%25C2%25A7MediaTRtrc465595%26filterCategoriesROOT%252FTelefon%25C2%25A7MediaTRtrc465595%3DCep%2BTelefonlar%25C4%25B1%25C2%25A7MediaTRtrc504171%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&sourceRef=INVALID',
            'Monitors': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%26filterCategoriesROOT%252FBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%3DMonit%25C3%25B6r%25C2%25A7MediaTRtrc639581%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}&sort=price&sourceRef=INVALID',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        category = category.format(search1='%2B'.join(search.split()), search2='+'.join(search.split()))
        url = 'https://www.mediamarkt.com.tr/tr/search.html?{}'.format(category)
        return url

    def get_product(self, product, search):
        products = []

        product_name = product.find("h1", {'itemprop': 'name'}).text.strip()
        if product.find("meta", {'itemprop': 'price'}):
            product_price = product.find("meta", {'itemprop': 'price'})['content'].split('.')[0] + ' TL'
        else:
            return products
        product_price_from = ''
        product_info = 'Ücretsiz Kargo' if product.find("span", {"data-layer": "deliveryinformation"}) else ''
        product_comment_count = product.find("div", "rating").findNext('span').text.strip() if product.find("div",
                                                                                                            "rating") else ''
        suitable_to_search = self.is_suitable_to_search(product_name, search)
        products.append(
            {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
             'old_price': product_price_from, 'info': product_info, 'comment_count': product_comment_count,
             'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)

        return products

    def get_products(self, content, search):
        products = []

        for product in content.find("ul", class_="products-list").find_all("li", recursive=False):
            if product.has_attr('class'):
                continue
            product_name = product.find("h2").text.strip()
            if product.find("div", class_='price small'):
                product_price = product.find("div", class_='price small').text.split(',')[0] + ' TL'
            else:
                continue
            product_price_from = product.find("div", class_='price price-xs price-old').text.split(',')[
                                     0] + ' TL' if product.find("div", class_='price price-xs price-old') else '1'
            product_info = ' '.join(
                product.find("span", {"data-layer": "deliveryinformation"}).parent.text.split()) if product.find("span",
                                                                                                                 {
                                                                                                                     "data-layer": "deliveryinformation"}) else ''
            product_comment_count = product.find("div", "rating").findNext('a').text.strip() if product.find("div",
                                                                                                             "rating") else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products
