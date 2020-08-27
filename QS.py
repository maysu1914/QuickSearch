from requests.utils import requote_uri
from bs4 import BeautifulSoup as soup
import requests
import math
import re

class Trendyol:
    base_url = "https://www.trendyol.com"
    source = '[Trendyol]'
    
    def __init__(self, category):
        self.category = category

    def search(self, search):
        self.search = search
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)

        if content.find("div","dscrptn") and "bulunamadı" not in content.find("div","dscrptn").text:
            page_number = math.ceil(int(re.findall('\d+', content.find("div","dscrptn").text)[0])/24)

            if page_number > 1:
                results += self.getProducts(content)
                for page in range(2, page_number + 1):
                    content = self.getContent(url + '&pi=' + str(page))
                    results += self.getProducts(content)
            else:
                results += self.getProducts(content)
        return results

    def getUrl(self, search):
        categories = {'Notebooks':'laptop','Smartphones':'akilli-cep-telefonu','All':'tum--urunler'}
        if self.category in categories:
            url = 'https://www.trendyol.com/{}?q={}&siralama=1'.format(categories[self.category],search)
##            print(url)
        else:
            url = self.base_url
        return requote_uri(url)
        
    def getContent(self, url):
        count = 10
        while count > 0:
            try:
                response = requests.get(url, timeout=10)
                count = 0
            except Exception as e:
                print(url,e)
                print("Trying...",count)
                count -= 1
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        
        for product in content.find_all("div","p-card-wrppr"):
            product_name = product.find("span","prdct-desc-cntnr-name").text.strip()
            if product.find("div","prc-box-dscntd"):
                product_price = product.find("div","prc-box-dscntd").text.split()[0].replace(".",'').split(',')[0]+ ' TL'
            elif product.find("div","prc-box-sllng"):
                product_price = product.find("div","prc-box-sllng").text.split()[0].replace(".",'').split(',')[0]+ ' TL'
            else:
                continue
            product_price_from = product.find("div","prc-box-orgnl").text.split()[0].replace(".",'').split(',')[0]+ ' TL' if product.find("div","prc-box-orgnl") is not None else ''
            product_info = product.find("div","stmp").text.strip() if product.find("div","stmp") is not None else ''
            product_comment_count = product.find("span","ratingCount").text.strip() if product.find("span","ratingCount") is not None else ''
            suitable_to_search = self.isSuitableToSearch(product_name,self.search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

    def isSuitableToSearch(self, product_name, search):
        search_words = re.findall('\d+', search)
        if any(word not in product_name for word in search_words):
            return False
        else:
            return True

class HepsiBurada:
    base_url = "https://www.hepsiburada.com"
    source = '[HepsiBurada]'
    
    def __init__(self, category):
        self.category = category

    def search(self, search):
        self.search = search
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)

        if not content.find("span","product-suggestions-title"):
            page_number = int(content.select("#pagination > ul > li")[-1].text.strip() if content.select("#pagination > ul > li") else 1)
##            print(page_number)
            if page_number > 1:
                results += self.getProducts(content)
                for page in range(2, page_number + 1):
                    content = self.getContent(url + '&sayfa=' + str(page))
                    results += self.getProducts(content)
            else:
                results += self.getProducts(content)

        return results

    def getUrl(self, search):
        categories = {'Notebooks':'&filtreler=MainCategory.Id:98','Smartphones':'&kategori=2147483642_371965','All':''}
        
        if self.category in categories:
            url = 'https://www.hepsiburada.com/ara?q={}{}&siralama=artanfiyat'.format(search,categories[self.category])
##            print(url)
        else:
            url = self.base_url
        return requote_uri(url)
        
    def getContent(self, url):
        count = 10
        while count > 0:
            try:
                response = requests.get(url, timeout=10)
                count = 0
            except Exception as e:
                print(url,e)
                print("Trying...",count)
                count -= 1
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        
        for product in content.find_all("div","product-detail"):
            if product.find("span","out-of-stock-icon"):
                continue
            product_name = product.find("h3","product-title").text.strip()
            if product.find("div","price-value"):
                product_price = product.find("div","price-value").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
            elif product.find("span","product-price"):
                product_price = product.find("span","product-price").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
            else: #if product.find("span","can-pre-order-text"): ÖN SIPARIS
                continue
            product_price_from = product.find("del","product-old-price").text.replace(",",".").split()[0].replace(".",'')[:-2]+ ' TL' if product.find("del","product-old-price") is not None else ''
            product_info = product.find("div","shipping-status").text.strip() if product.find("div","shipping-status") is not None else ''
            product_comment_count = product.find("span","number-of-reviews").text.strip() if product.find("span","number-of-reviews") is not None else ''
            suitable_to_search = self.isSuitableToSearch(product_name,self.search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

    def isSuitableToSearch(self, product_name, search):
        search_words = re.findall('\d+', search)
        if any(word not in product_name for word in search_words):
            return False
        else:
            return True

class n11:
    base_url = "https://www.n11.com"
    source = '[n11]'
    
    def __init__(self, category):
        self.category = category

    def search(self, search):
        self.search = search
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)

        if not content.find("span","result-mean-word") and not content.select('#error404') and not content.select('#searchResultNotFound') and not content.select('.noResultHolder'):
            page_number = math.ceil(int(content.select(".resultText > strong")[0].text.replace(",",""))/28)
            if page_number > 50:
                page_number = 50
            if page_number > 1:
                results += self.getProducts(content)
                for page in range(2, page_number + 1):
                    content = self.getContent(url + '&pg=' + str(page))
                    results += self.getProducts(content)
            else:
                results += self.getProducts(content)

        return results

    def getUrl(self, search):
        categories = {'Notebooks':'bilgisayar/dizustu-bilgisayar','Smartphones':'telefon-ve-aksesuarlari/cep-telefonu','All':'arama'}
        
        if self.category in categories:
            url = 'https://www.n11.com/{}?q={}&srt=PRICE_LOW'.format(categories[self.category],'+'.join(search.split()))
##            print(url)
        else:
            url = self.base_url
            
        return requote_uri(url)

    def getContent(self, url):
        count = 10
        while count > 0:
            try:
                response = requests.get(url, timeout=10)
                count = 0
            except Exception as e:
                print(url,e)
                print("Trying...",count)
                count -= 1
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        for product in content.select("#view ul")[0].find_all("div","columnContent"):
            product_name = product.find("h3","productName").text.strip()
            product_price = product.find("a","newPrice").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
            product_price_from = product.find("a","oldPrice").text.replace(",",".").split()[0].replace(".",'')[:-2]+ ' TL' if product.find("a","oldPrice") is not None else ''
            product_info = 'Ücretsiz Kargo' if product.find("span","freeShipping") is not None else ''
            product_comment_count = product.find("span","ratingText").text.strip() if product.find("span","ratingText") is not None else ''
            suitable_to_search = self.isSuitableToSearch(product_name,self.search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

    def isSuitableToSearch(self, product_name, search):
        search_words = re.findall('\d+', search)
        if any(word not in product_name for word in search_words):
            return False
        else:
            return True
    
class VatanBilgisayar:
    base_url = "https://www.vatanbilgisayar.com"
    source = '[VatanBilgisayar]'
    
    def __init__(self, category):
        self.category = category

    def search(self, search):
        self.search = search
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)
        
        if not content.find("div","empty-basket"):
            for page in content.find("ul", "pagination").find_all("li"):
                if 'active' in page['class']:
                    results += self.getProducts(content)
                elif page.find("span","icon-angle-right"):
                    break
                else:
                    content = self.getContent(self.base_url + page.find("a")['href'])
                    results += self.getProducts(content)

        return results

    def getUrl(self, search):
        categories = {'Notebooks':'notebook/','Smartphones':'cep-telefonu-modelleri/','All':''}
        
        if self.category in categories:
            url = 'https://www.vatanbilgisayar.com/arama/{}/{}?srt=UP'.format(search,categories[self.category])
##            print(url)
        else:
            url = self.base_url
        
        return requote_uri(url)

    def getContent(self, url):
        count = 10
        while count > 0:
            try:
                response = requests.get(url, timeout=10)
                count = 0
            except Exception as e:
                print(url,e)
                print("Trying...",count)
                count -= 1
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        for product in content.find_all("div","product-list--list-page"):
            product_name = product.find("div","product-list__product-name").text.strip()
            product_code = product.find("div","product-list__product-code").text.strip()
            product_price = product.find("span","product-list__price").text.strip().replace(".",'')+ ' TL'
            product_price_from = product.find("span","product-list__current-price").text.strip().replace(".",'')+ ' TL'
            product_stock = product.find("span","wrapper-condition__text").text.strip() if product.find("span","wrapper-condition__text") else ''
            product_comment_count = product.find("a","comment-count").text.strip()
            suitable_to_search = self.isSuitableToSearch(product_name,self.search)
            products.append({'source':self.source, 'name':product_name,'code':product_code,'price':product_price,'old_price':product_price_from,'info':product_stock,'comment_count':product_comment_count,'suitable_to_search':suitable_to_search})
##            print(product_name,product_code,product_price,product_price_from,product_stock,product_comment_count)
        return products

    def isSuitableToSearch(self, product_name, search):
        search_words = re.findall('\d+', search)
        if any(word not in product_name for word in search_words):
            return False
        else:
            return True
            
def sourceController(category):
##    print(category)
    sources = {'VatanBilgisayar':VatanBilgisayar, 'n11':n11, 'HepsiBurada':HepsiBurada, 'Trendyol':Trendyol}
    source_selection = None
    results = []
    correct_results = []
    near_results = []

    print("\nSelect the sources you want to search?")
    for index, source in zip(range(1,len(sources)+1),sources):
        print(str(index)+'.',source)
    while source_selection == None or any(source not in [str(num) for num in range(0,len(sources)+1)] for source in source_selection):
        source_selection = [source.strip() for source in input('Sources: ').split(',')]
        if '0' in source_selection:
            source_selection = [str(num) for num in range(1,len(sources)+1)]

##    print(source_selection)
    
    search_input = input('\nSearch Text: ').strip()

    for source in source_selection:
        results += list(sources.values())[int(source)-1](category).search(search_input)

    for i in sorted(results, key = lambda i: [-i['suitable_to_search'], int(i['price'].split()[0])]):
        if i['suitable_to_search']:
            correct_results.append(i)
        else:
            near_results.append(i)
    print("\nResults:") if correct_results else ''
    for product in correct_results:
        print(product['source'], product['name'], product['price'], product['info'],product['comment_count'])

    print("\nYou may want to look at these:") if near_results else ''
    for product in near_results:
        print(product['source'], product['name'], product['price'], product['info'],product['comment_count'])

    print("_________________________________\n")


def main():
    categories = ['All', 'Notebooks', 'Smartphones']
    category_selection = None

    print("What category do you want to search?")
    for index in range(1,len(categories)):
        print(str(index)+'.',categories[index])
    while category_selection not in [str(num) for num in range(0,len(categories))]:
        category_selection = input('Category: ').strip()

    sourceController(categories[int(category_selection)])
    
if __name__ == "__main__":
    while True:
        main()
