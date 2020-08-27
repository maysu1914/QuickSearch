from requests.utils import requote_uri
from bs4 import BeautifulSoup as soup
from concurrent.futures import ProcessPoolExecutor as Pool
import itertools
import requests
import math
import re
##import os

class SourceWebSite():
    def __init__(self, category):
        self.category = category

    def search(self, search):
        self.search = search
        urls = self.getUrl(search)
        results = []
        for url in urls:
            results += self.getResults(results, url)
        return results

    def getUrl(self, search):
        categories = self.getCategories()

        if '[' in search and ']' in search:
            if self.category in categories:
                urls = []
                static = search
                dynamic = []
                
                for a,b in zip(range(1,search.count('[')+1),range(1,search.count(']')+1)):
                    start = self.find_nth(search, '[', a)
                    end = self.find_nth(search, ']', a) + 1
                    part = search[start:end]
                    dynamic.append(part.strip('][').split(','))
                    static = static.replace(part,'')

                for i in list(itertools.product(*dynamic)):
                    search = (' '.join(static.split()) + ' ' + ' '.join(i)).strip()
                    url = self.createUrl(search, categories[self.category])
                    urls.append({'search':search,'url':requote_uri(url)})
##                    print(url)
                return urls
            else:
                return []
        else:
            if self.category in categories:
                url = self.createUrl(search, categories[self.category])
##                print(url)
                return [{'search':search,'url':requote_uri(url)}]
            else:
                return []

    def find_nth(self, haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start

    def getResult(self, url, search):
        content = self.getContent(url)
        result = self.getProducts(content, search)
        return result
        
    def getContent(self, url):
        print(url)
        count = 10
        while count > 0:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
                response = requests.get(url, timeout=10, headers=headers)
##                print(response.url)
##                print(response.content)
                count = 0
            except Exception as e:
                print(url,e)
                print("Trying...",count)
                count -= 1
                if count == 0:
                    response = ''
        return soup(response.content, "lxml")

    def isSuitableToSearch(self, product_name, search):
        product_name = product_name.lower()
        search = search.lower()
        
        search_numbers = re.findall('\d+', search)
        search_words = search.lower()

        for number in search_numbers:
            search_words = search_words.replace(number,'')
            
        search_words = [word if len(word)>2 else None for word in search_words.split()]

        search_words = [i for i in search_words if i] 
    
        for number in search_numbers:
            count = search.count(number)
            if product_name.count(number) < count:
                return False
        for word in search_words:
            count = search.count(word)
            if product_name.count(word) < count:
                return False
        return True

class Teknosa(SourceWebSite):
    base_url = "https://www.teknosa.com"
    source = '[Teknosa]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])

        if not content.find("i","icon-search-circle"):
            page_number = int(content.find("ul","pagination").find_all("li")[-2].text if content.find("ul","pagination") else '1')

            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(1, page_number)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()
        return results

    def getCategories(self):
        categories = {'Notebooks':':relevance:category:1020101','Smartphones':':relevance:category:100001','All':':relevance'}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.teknosa.com/arama/?q={}{}&sort=price-asc'.format(search, category)
        return url

    def getProducts(self, content, search):
        products = []
        
        for product in content.find_all("div","product-item"):
            product_name = product.find("div","product-name").text.strip()
            if product.find("span", class_='price-tag new-price font-size-tertiary'):
                product_price = product.find("span", class_='price-tag new-price font-size-tertiary').text.split()[0].split(',')[0].replace('.','') + ' TL'
            else:
                continue
            product_price_from = product.find("span", class_='price-tag old-price block').text.split()[0].split(',')[0].replace('.','') + ' TL' if product.find("span", class_='price-tag old-price block') else ''
            product_info = 'KARGO BEDAVA' if int(product_price.split()[0]) > 100 else ''
            product_comment_count = ''
            suitable_to_search = self.isSuitableToSearch(product_name,search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

class AmazonTR(SourceWebSite):
    base_url = "https://www.amazon.com.tr"
    source = '[AmazonTR]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])

        if any("Şunu mu demek istediniz" in i.text for i in content.select("span.a-size-medium.a-color-base.a-text-normal")):
            url['url'] = self.base_url + content.select("a.a-size-medium.a-link-normal.a-text-bold.a-text-italic")[0]['href']
            content = self.getContent(url['url'])

        if content.find(cel_widget_id="MAIN-SEARCH_RESULTS"):# and 'sonuç yok' not in content.find(cel_widget_id='MAIN-TOP_BANNER_MESSAGE').text:
            page_number = int(content.find("ul","a-pagination").find_all("li")[-2].text if content.find("ul","a-pagination") else '1')

            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()
        return results

    def getCategories(self):
        categories = {'Notebooks':'&i=computers&rh=n%3A12466439031%2Cn%3A12601898031','Smartphones':'&i=electronics&rh=n%3A12466496031%2Cn%3A13709907031','All':''}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.amazon.com.tr/s?k={}{}&s=price-asc-rank'.format('+'.join(search.split()), category)
        return url

    def getProducts(self, content, search):
        products = []
        
        for product in content.find_all("span",cel_widget_id="MAIN-SEARCH_RESULTS"):
            if product.find("span", class_='a-size-medium a-color-base a-text-normal'):
                product_name = product.find("span", class_='a-size-medium a-color-base a-text-normal').text.strip()
            else:
                product_name = product.find("span", class_='a-size-base-plus a-color-base a-text-normal').text.strip()
            if product.find("span","a-price-whole"):
                product_price = product.find("span","a-price-whole").text.split()[0].replace(".",'').split(',')[0]+ ' TL'
            else:
                continue
            product_price_from = product.select("span.a-price.a-text-price")[0].text.replace("₺",'').replace(".",'').split(',')[0]+ ' TL' if len(product.select("span.a-price.a-text-price")) > 0 else ''
            product_info = ('Kargo BEDAVA' if 'BEDAVA' in product.select(".a-row.a-size-base.a-color-secondary.s-align-children-center")[0].text else '') if len(product.select(".a-row.a-size-base.a-color-secondary.s-align-children-center")) > 0 else ''
            product_comment_count = product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small span")[-1].text.strip() if len(product.select(".a-section.a-spacing-none.a-spacing-top-micro .a-row.a-size-small")) > 0 else ''
            suitable_to_search = self.isSuitableToSearch(product_name,search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

class Trendyol(SourceWebSite):
    base_url = "https://www.trendyol.com"
    source = '[Trendyol]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])

        if content.find("div","dscrptn") and "bulunamadı" not in content.find("div","dscrptn").text:
            page_number = math.ceil(int(re.findall('\d+', content.find("div","dscrptn").text)[0])/24)

            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pi=' + str(number) for number in range(2, page_number + 1)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()
        return results

    def getCategories(self):
        categories = {'Notebooks':'laptop','Smartphones':'akilli-cep-telefonu','All':'tum--urunler'}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.trendyol.com/{}?q={}&siralama=1'.format(category,search)
        return url

    def getProducts(self, content, search):
        products = []
        
        for product in content.find_all("div","p-card-wrppr"):
            product_brand = product.find("span","prdct-desc-cntnr-ttl").text.strip() if product.find("span","prdct-desc-cntnr-ttl") else ''
            product_name = product_brand + ' ' + product.find("span","prdct-desc-cntnr-name").text.strip()
            if product.find("div","prc-box-dscntd"):
                product_price = product.find("div","prc-box-dscntd").text.split()[0].replace(".",'').split(',')[0]+ ' TL'
            elif product.find("div","prc-box-sllng"):
                product_price = product.find("div","prc-box-sllng").text.split()[0].replace(".",'').split(',')[0]+ ' TL'
            else:
                continue
            product_price_from = product.find("div","prc-box-orgnl").text.split()[0].replace(".",'').split(',')[0]+ ' TL' if product.find("div","prc-box-orgnl") is not None else ''
            product_info = product.find("div","stmp").text.strip() if product.find("div","stmp") is not None else ''
            product_comment_count = product.find("span","ratingCount").text.strip() if product.find("span","ratingCount") is not None else ''
            suitable_to_search = self.isSuitableToSearch(product_name, search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

class HepsiBurada(SourceWebSite):
    base_url = "https://www.hepsiburada.com"
    source = '[HepsiBurada]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])

        if not content.find("span","product-suggestions-title"):
            page_number = int(content.select("#pagination > ul > li")[-1].text.strip() if content.select("#pagination > ul > li") else 1)

            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&sayfa=' + str(number) for number in range(2, page_number + 1)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()
        return results

    def getCategories(self):
        categories = {'Notebooks':'&filtreler=MainCategory.Id:98','Smartphones':'&kategori=2147483642_371965','All':''}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.hepsiburada.com/ara?q={}{}&siralama=artanfiyat'.format(search, category)
        return url

    def getProducts(self, content, search):
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
            suitable_to_search = self.isSuitableToSearch(product_name, search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products

class n11(SourceWebSite):
    base_url = "https://www.n11.com"
    source = '[n11]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])

        if not content.find("span","result-mean-word") and not content.select('#error404') and not content.select('#searchResultNotFound') and not content.select('.noResultHolder'):
            page_number = math.ceil(int(content.select(".resultText > strong")[0].text.replace(",",""))/28)
            page_number = 50 if page_number > 50 else page_number

            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&pg=' + str(number) for number in range(2, page_number + 1)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()
        return results
            
    def getCategories(self):
        categories = {'Notebooks':'bilgisayar/dizustu-bilgisayar','Smartphones':'telefon-ve-aksesuarlari/cep-telefonu','All':'arama'}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.n11.com/{}?q={}&srt=PRICE_LOW'.format(category,'+'.join(search.split()))
        return url

    def getProducts(self, content, search):
        products = []
        for product in content.select("#view ul")[0].find_all("div","columnContent"):
            product_name = product.find("h3","productName").text.strip()
            product_price = product.find("a","newPrice").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
            product_price_from = product.find("a","oldPrice").text.replace(",",".").split()[0].replace(".",'')[:-2]+ ' TL' if product.find("a","oldPrice") is not None else ''
            product_info = 'Ücretsiz Kargo' if product.find("span","freeShipping") is not None else ''
            product_comment_count = product.find("span","ratingText").text.strip() if product.find("span","ratingText") is not None else ''
            suitable_to_search = self.isSuitableToSearch(product_name, search)
            products.append({'source':self.source, 'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count, 'suitable_to_search':suitable_to_search})
##            print(product_name,product_price,product_info,product_comment_count)
        return products
    
class VatanBilgisayar(SourceWebSite):
    base_url = "https://www.vatanbilgisayar.com"
    source = '[VatanBilgisayar]'

    def getResults(self, results, url):
        content = self.getContent(url['url'])
        
        if not content.find("div","empty-basket"):
            page_number = int(content.find("ul", "pagination").find_all("li")[-2].text.strip()) if len(content.find("ul", "pagination").find_all("li")) > 1 else 1
            page_number = 50 if page_number > 50 else page_number
            
            results += self.getProducts(content, url['search'])
            if page_number > 1:
                page_list = [url['url'] + '&page=' + str(number) for number in range(2, page_number + 1)]
                processes = []
                with Pool() as pool:
                    for page in page_list:
                        processes.append(pool.submit(self.getResult, page, url['search']))
                    for process in processes:
                        results += process.result()                   
        return results

    def getCategories(self):
        categories = {'Notebooks':'notebook/','Smartphones':'cep-telefonu-modelleri/','All':''}
        return categories

    def createUrl(self, search, category):
        url = 'https://www.vatanbilgisayar.com/arama/{}/{}?srt=UP'.format(search, category)
        return url

    def getProducts(self, content, search):
        products = []
        for product in content.find_all("div","product-list--list-page"):
            product_name = product.find("div","product-list__product-name").text.strip()
            product_code = product.find("div","product-list__product-code").text.strip()
            product_price = product.find("span","product-list__price").text.strip().replace(".",'')+ ' TL'
            product_price_from = product.find("span","product-list__current-price").text.strip().replace(".",'')+ ' TL'
            product_stock = product.find("span","wrapper-condition__text").text.strip() if product.find("span","wrapper-condition__text") else ''
            product_comment_count = product.find("a","comment-count").text.strip()
            suitable_to_search = self.isSuitableToSearch(product_name, search)
            products.append({'source':self.source, 'name':product_name,'code':product_code,'price':product_price,'old_price':product_price_from,'info':product_stock,'comment_count':product_comment_count,'suitable_to_search':suitable_to_search})
##            print(product_name,product_code,product_price,product_price_from,product_stock,product_comment_count)
        return products
            
def sourceController(category):
    sources = {'VatanBilgisayar':VatanBilgisayar, 'n11':n11, 'HepsiBurada':HepsiBurada, 'Trendyol':Trendyol, 'AmazonTR':AmazonTR, 'Teknosa':Teknosa}
    source_selection = None
    results = []
    correct_results = []
    near_results = []

    print("\nSelect the sources you want to search:")
    for index, source in zip(range(1,len(sources)+1),sources):
        print(str(index)+'.',source)
    while source_selection == None or any(source not in [str(num) for num in range(0,len(sources)+1)] for source in source_selection):
        source_selection = [source.strip() for source in input('Sources: ').split(',')]
        if '0' in source_selection:
            source_selection = [str(num) for num in range(1,len(sources)+1)]
    
    search_input = input('\nSearch Text: ').strip()

    for source in source_selection:
        results += list(sources.values())[int(source)-1](category).search (search_input)

    unique_results = []
    seen = set()
    for result in results:
        t = tuple(result.items())
        if t not in seen:
            seen.add(t)
            unique_results.append(result)

    for i in sorted(unique_results, key = lambda i: [-i['suitable_to_search'], int(i['price'].split()[0])]):
        if i['suitable_to_search']:
            correct_results.append(i)
        else:
            t = i.copy()
            t['suitable_to_search'] = True
            t = tuple(t.items())
            if t not in seen:
                near_results.append(i)
            else:
##                print(i)
                pass

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
