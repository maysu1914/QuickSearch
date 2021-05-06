from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class MediaMarktTR(SourceWebSite):
    base_url = "https://www.mediamarkt.com.tr"
    source_name = 'MediaMarktTR'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and soup.find("ul", "products-list"):
            page_number = self.get_page_number(soup.find("ul", "pagination"))
            results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                contents = self.get_contents(page_list)
                for content in contents:
                    results += self.get_products(content, url['search'])
            else:
                pass
        elif soup and soup.find("div", id="product-details"):
            results += self.get_product(content, url['search'])
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
            'All': 'query={search2}&searchProfile=onlineshop&channel=mmtrtr',
            'Notebooks': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DTa%25C5%259F%25C4%25B1nabilir%2BBilgisayarlar%25C2%25A7MediaTRtrc504926%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Desktop PCs': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%25C2%25A7MediaTRtrc504925%26filterCategoriesROOT%252FBilgisayar%25C2%25A7MediaTRtrc504925%3DMasa%25C3%25BCst%25C3%25BC%2BBilgisayarlar%25C2%25A7MediaTRtrc504957%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Smartphones': 'searchParams=%2FSearch.ff%3Fquery%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DTelefon%25C2%25A7MediaTRtrc465595%26filterCategoriesROOT%252FTelefon%25C2%25A7MediaTRtrc465595%3DCep%2BTelefonlar%25C4%25B1%25C2%25A7MediaTRtrc504171%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Monitors': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%26filterCategoriesROOT%252FBilgisayar%2BBile%25C5%259Fenleri%25C2%25A7MediaTRtrc639556%3DMonit%25C3%25B6r%25C2%25A7MediaTRtrc639581%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
            'Digital Cameras': 'searchParams=/Search.ff?query%3D{search1}%26filterTabbedCategory%3Donlineshop%26filteravailability%3D1%26filterCategoriesROOT%3DFoto%2B%2526%2BKamera%25C2%25A7MediaTRtrc465682%26filterCategoriesROOT%252FFoto%2B%2526%2BKamera%25C2%25A7MediaTRtrc465682%3DFoto%25C4%259Fraf%2BMakineleri%25C2%25A7MediaTRtrc465683%26channel%3Dmmtrtr%26productsPerPage%3D20%26disableTabbedCategory%3Dtrue&searchProfile=onlineshop&query={search2}',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        category = category.format(search1='%2B'.join(search.split()), search2='+'.join(search.split()))
        url = 'https://www.mediamarkt.com.tr/tr/search.html?{}&sort=price&sourceRef=INVALID'.format(category)
        return url

    def get_product(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        data = {}
        data['source'] = '[{}]'.format(self.source_name)
        data['name'] = self.get_product_name(soup.find("h1", {'itemprop': 'name'}))
        data['price'] = self.get_product_price(soup.select("div.price.big"))
        data['old_price'] = None
        data['info'] = self.get_product_info(soup.select("div.price-details > small"))
        data['comment_count'] = self.get_product_comment_count(soup.select("dd.product-rate > span.clickable > span"))
        data['suitable_to_search'] = self.is_suitable_to_search(data['name'], search)
        return [data]

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.select("ul.products-list > li:not([class])"):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("h2"))
            data['price'] = self.get_product_price(product.select("div.price.small"))
            data['old_price'] = self.get_product_old_price(product.select("div.price.price-old"))
            data['info'] = self.get_product_info(product.select("div.price-box > small"))
            data['comment_count'] = self.get_product_comment_count(product.select("span.see-reviews"))
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
            return int(element[0].text.split(',')[0])
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            return int(element[0].text.split(',')[0])
        else:
            return None

    def get_product_info(self, element):
        if element:
            if element[0].find("img"):
                return 'Ücretsiz Kargo'
            else:
                return element[0].text.strip()
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            return element[0].text.strip()
        else:
            return None
