from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .SourceWebSite import SourceWebSite


class AmazonTR(SourceWebSite):
    base_url = "https://www.amazon.com.tr"
    source_name = 'AmazonTR'

    def get_results(self, url):
        content = self.get_page_content(url['url'])
        soup = BeautifulSoup(content, "lxml")
        results = []

        if soup and self.is_did_you_mean(soup.select("span.a-size-medium.a-color-base.a-text-normal")):
            pathname = soup.select("a.a-size-medium.a-link-normal.a-text-bold.a-text-italic")[0]['href']
            url['url'] = urljoin(self.base_url, pathname)
            content = self.get_page_content(url['url'])
            soup = BeautifulSoup(content, "lxml")
        else:
            pass

        if soup and self.is_product_list_page(soup):
            page_number = self.get_page_number(soup.find("ul", "a-pagination"))
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

    def is_product_list_page(self, page):
        no_results_all = page.find("span", class_='a-size-medium a-color-base')
        no_results_category = page.find("h3", class_='a-size-base a-spacing-base a-color-base a-text-normal')
        if no_results_all:
            return False
        elif no_results_category and 'sonuç bulunamadı' in no_results_category.text:
            return False
        else:
            return True

    def is_did_you_mean(self, element):
        return any("Şunu mu demek istediniz" in i.text for i in element)

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
            'Notebooks': '&i=computers&rh=n%3A12466439031%2Cn%3A12601898031',
            'Desktop PCs': '&i=computers&rh=n%3A12601903031',
            'Smartphones': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709907031',
            'Monitors': '&i=computers&rh=n%3A12466439031%2Cn%3A12601904031',
            'Digital Cameras': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709883031%2Cn%3A13709933031',
            'Shoes': '&i=fashion&rh=n%3A12466553031',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.amazon.com.tr/s?k={}{}&s=price-asc-rank'.format('+'.join(search.split()), category)
        return url

    def get_products(self, content, search):
        soup = BeautifulSoup(content, "lxml")
        products = []

        for product in soup.find_all("div", {"data-component-type": "s-search-result"}):
            data = {}
            data['source'] = '[{}]'.format(self.source_name)
            data['name'] = self.get_product_name(product.find("a", class_='a-link-normal a-text-normal'))
            data['price'] = self.get_product_price(product.find("span", "a-price-whole"))
            data['old_price'] = self.get_product_old_price(product.select("span.a-price.a-text-price"))
            data['info'] = self.get_product_info(product.select(".a-row.a-size-base.a-color-secondary"))
            data['comment_count'] = self.get_product_comment_count(product.select(".a-spacing-top-micro .a-size-small"))
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
            price = element.text.split(',')[0].replace('.', '')
            return int(price)
        else:
            return None

    def get_product_old_price(self, element):
        if element:
            if len(element) > 0:
                old_price = element[0].text.strip()[0].replace('.', '')
                return int(old_price)
            else:
                return None
        else:
            return None

    def get_product_info(self, element):
        if element:
            if 'BEDAVA' in element[0].text:
                return 'Kargo BEDAVA'
            else:
                return None
        else:
            return None

    def get_product_comment_count(self, element):
        if element:
            comment_count = element[0].text.split()[-1]
            if comment_count.isdigit():
                return comment_count
            else:
                return None
        else:
            return None
