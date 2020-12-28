from .SourceWebSite import SourceWebSite


class AmazonTR(SourceWebSite):
    base_url = "https://www.amazon.com.tr"
    source_name = 'AmazonTR'

    def get_results(self, url):
        content = self.get_content(url['url'])

        if content and any("Şunu mu demek istediniz" in i.text for i in
                           content.select("span.a-size-medium.a-color-base.a-text-normal")):
            url['url'] = self.base_url + content.select("a.a-size-medium.a-link-normal.a-text-bold.a-text-italic")[0][
                'href']
            content = self.get_content(url['url'])
        else:
            pass

        if content and not (content.find("span", class_='a-size-medium a-color-base') or (content.find("h3",
                                                                                                       class_='a-size-base a-spacing-base a-color-base a-text-normal') and 'sonuç bulunamadı' in content.find(
            "h3", class_='a-size-base a-spacing-base a-color-base a-text-normal').text)):
            page_number = int(content.find("ul", "a-pagination").find_all("li")[-2].text if content.find("ul",
                                                                                                         "a-pagination") else '1')
            page_number = self.max_page if page_number > self.max_page else page_number

            self.results += self.get_products(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
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
            'Notebooks': '&i=computers&rh=n%3A12466439031%2Cn%3A12601898031',
            'Smartphones': '&i=electronics&rh=n%3A12466496031%2Cn%3A13709907031',
            'Monitors': '&i=computers&rh=n%3A12466439031%2Cn%3A12601904031',
            'Shoes': '&i=fashion&rh=n%3A12466553031',
        }
        return categories

    @staticmethod
    def create_url(search, category):
        url = 'https://www.amazon.com.tr/s?k={}{}&s=price-asc-rank'.format('+'.join(search.split()), category)
        return url

    def get_products(self, content, search):
        products = []

        for product in content.find_all("div", {"data-component-type": "s-search-result"}):
            if product.find("span", class_='a-size-medium a-color-base a-text-normal'):
                product_name = product.find("span", class_='a-size-medium a-color-base a-text-normal').text.strip()
            else:
                product_name = product.find("span", class_='a-size-base-plus a-color-base a-text-normal').text.strip()
            if product.find("span", "a-price-whole"):
                product_price = product.find("span", "a-price-whole").text.split()[0].replace(".", '').split(',')[
                                    0] + ' TL'
            else:
                continue
            product_price_from = \
                product.select("span.a-price.a-text-price")[0].text.replace("₺", '').replace(".", '').split(',')[
                    0] + ' TL' if len(product.select("span.a-price.a-text-price")) > 0 else ''
            product_info = ('Kargo BEDAVA' if 'BEDAVA' in product.select(
                ".a-row.a-size-base.a-color-secondary.s-align-children-center")[0].text else '') if len(
                product.select(".a-row.a-size-base.a-color-secondary.s-align-children-center")) > 0 else ''
            product_comment_count = \
                product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small span")[
                    -1].text.strip() if len(
                    product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small")) > 0 else ''
            suitable_to_search = self.is_suitable_to_search(product_name, search)
            products.append(
                {'source': '[{}]'.format(self.source_name), 'name': product_name, 'code': None, 'price': product_price,
                 'old_price': product_price_from, 'info': product_info,
                 'comment_count': product_comment_count, 'suitable_to_search': suitable_to_search})
        # print(product_name,product_price,product_info,product_comment_count)
        return products
