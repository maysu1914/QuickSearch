from requests.utils import requote_uri
from bs4 import BeautifulSoup as soup
import requests
import math

class HepsiBurada:
    base_url = "https://www.hepsiburada.com"
    
    def __init__(self, mode):
        self.mode = mode

    def search(self, search):
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)

        page_number = int(content.select("#pagination > ul > li")[-1].text.strip() if content.select("#pagination > ul > li") else 1)

        if page_number > 1:
            results += self.getProducts(content)
            for page in range(2, page_number + 1):
                content = self.getContent(url + '&sayfa=' + str(page))
                results += self.getProducts(content)
        else:
            results += self.getProducts(content)

        return results

    def getUrl(self, search):
        if self.mode == 'free':
            return self.getFreeUrl(search)
##        elif self.mode == 'manual':
##            return self.getManualUrl(search)

    def getFreeUrl(self, search):
        url = 'https://www.hepsiburada.com/ara?q={}&filtreler=MainCategory.Id:98'.format(search)
        return requote_uri(url)

##    def getManualUrl(self, search):
##        pass

    def getContent(self, url):
        response = None
        while response == None:
            try:
                response = requests.get(url, timeout=10)
            except Exception as e:
                print(url,e)
                print("Trying...")
                response = None
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        if not content.find("span","product-suggestions-title"):
            for product in content.find_all("div","product-detail"):
                product_name = product.find("h3","product-title").text.strip()
                if product.find("div","price-value"):
                    product_price = product.find("div","price-value").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
                else:
                    product_price = product.find("span","product-price").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
                product_price_from = product.find("del","product-old-price").text.replace(",",".").split()[0].replace(".",'')[:-2]+ ' TL' if product.find("del","product-old-price") is not None else ''
                product_info = product.find("div","shipping-status").text.strip() if product.find("div","shipping-status") is not None else ''
                product_comment_count = product.find("span","number-of-reviews").text.strip() if product.find("span","number-of-reviews") is not None else ''
                products.append({'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count})
##                print(product_name,product_price,product_info,product_comment_count)
        return products

class n11:
    base_url = "https://www.n11.com"
    
    def __init__(self, mode):
        self.mode = mode

    def search(self, search):
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)
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
        if self.mode == 'free':
            return self.getFreeUrl(search)
##        elif self.mode == 'manual':
##            return self.getManualUrl(search)

    def getFreeUrl(self, search):
        url = 'https://www.n11.com/bilgisayar/dizustu-bilgisayar?q={}&srt=PRICE_LOW'.format('+'.join(search.split()))
        return requote_uri(url)

##    def getManualUrl(self, search):
##        pass

    def getContent(self, url):
        response = None
        while response == None:
            try:
                response = requests.get(url, timeout=10)
            except Exception as e:
                print(url,e)
                print("Trying...")
                response = None
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        for product in content.select("#view ul")[0].find_all("div","columnContent"):
            product_name = product.find("h3","productName").text.strip()
            product_price = product.find("a","newPrice").text.replace(",",".").replace('"','').split()[0].replace(".",'')[:-2]+ ' TL'
            product_price_from = product.find("a","oldPrice").text.replace(",",".").split()[0].replace(".",'')[:-2]+ ' TL' if product.find("a","oldPrice") is not None else ''
            product_info = 'Ücretsiz Kargo' if product.find("span","freeShipping") is not None else ''
            product_comment_count = product.find("span","ratingText").text.strip() if product.find("span","ratingText") is not None else ''
            products.append({'name':product_name,'code':None,'price':product_price,'old_price':product_price_from,'info':product_info,'comment_count':product_comment_count})
##            print(product_name,product_price,product_info,product_comment_count)
        return products
class VatanBilgisayar:
    base_url = "https://www.vatanbilgisayar.com"
    
    def __init__(self, mode):
        self.mode = mode

    def search(self, search):
        url = self.getUrl(search)
        results = []

        content = self.getContent(url)
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
        if self.mode == 'free':
            return self.getFreeUrl(search)
##            print(search)
##        elif self.mode == 'manual':
##            return self.getManualUrl(search)

    def getFreeUrl(self, search):
        url = 'https://www.vatanbilgisayar.com/arama/{}/notebook/?srt=UP'.format(search)
##        print(url)
        return requote_uri(url)

##    def getManualUrl(self, search):
##        urls = []
##        filter1 = r'/'
##        filter2 = '?opf={}'
##        filter3 = '&qText={}'.format(search['keyword'])
##        url = 'https://www.vatanbilgisayar.com{}/notebook/'
##        if '8' in search['ram']:
##            filter1 += '8gb-ram-'
##            filter2 = filter2.format('p11821,{}')
##        elif '16' in search['ram']:
##            filter1 += '16gb-ram-'
##            filter2 = filter2.format('p11820,{}')
##        elif '32' in search['ssd']:
##            filter1 += '32gb-ram-'
##            filter2 = filter2.format('p16878,{}')
##            
##        if '128' in search['ssd']:
##            filter1 += '128gb'
##            filter2 = filter2.format('p16014')
##        elif '256' in search['ssd']:
##            filter1 += '256gb'
##            filter2 = filter2.format('p14203')
##        elif '512' in search['ssd']:
##            filter1 = ''
##            filter2 = filter2.format('p1403,p19591')
##        return requote_uri(url.format(filter1)+filter2+filter3+'&srt=UP')

    def getContent(self, url):
        response = None
        while response == None:
            try:
                response = requests.get(url, timeout=10)
            except Exception as e:
                print(url,e)
                print("Trying...")
                response = None
        return soup(response.content, "lxml")

    def getProducts(self, content):
        products = []
        for product in content.find_all("div","product-list--list-page"):
            product_name = product.find("div","product-list__product-name").text.strip()
            product_code = product.find("div","product-list__product-code").text.strip()
            product_price = product.find("span","product-list__price").text.strip().replace(".",'')+ ' TL'
            product_price_from = product.find("span","product-list__current-price").text.strip().replace(".",'')+ ' TL'
            product_stock = product.find("span","wrapper-condition__text").text.strip()
            product_comment_count = product.find("a","comment-count").text.strip()
            products.append({'name':product_name,'code':product_code,'price':product_price,'old_price':product_price_from,'info':product_stock,'comment_count':product_comment_count})
##            print(product_name,product_code,product_price,product_price_from,product_stock,product_comment_count)
        return products
            
def freeMode():
    sources = {'Vatan Bilgisayar':VatanBilgisayar, 'n11':n11, 'Hepsi Burada':HepsiBurada}
    source_selection = None
    results = []

    print("\nSelect the sources you want to search in notebooks?")
    for index, source in zip(range(1,len(sources)+1),sources):
        print(str(index)+'.',source)
    while source_selection == None or any(source not in [str(num) for num in range(1,len(sources)+1)] for source in source_selection):
        source_selection = [source.strip() for source in input('Sources: ').split(',')]
    
    search_input = input('\nSearch Text: ').strip()

    for source in source_selection:
        results += list(sources.values())[int(source)-1]('free').search(search_input)

    for i in sorted(results, key = lambda i: int(i['price'].split()[0])):
        print(i['name'],i['price'],i['info'],i['comment_count'])

    print("_________________________________\n")

##def manualMode():
##    vatan_bilgisayar = VatanBilgisayar('manual')
##    ssd_capacities = {'low':['120','128'],'medium':['240','250','256'],'high':['500','512']}
##    ram_capacities = {'low':['4'],'medium':['8'],'high':['16'],'ultra':['32','64']}
##    search_data = {'keyword':'','ram':'','ssd':''}
##    ssd_input = None
##    ram_input = None
##
##    keyword_input = input('Keyword: ').strip()
##
##    while ssd_input is None:
##        temp_input = input('SSD Capacity (GB): ').strip()
##        for level in ssd_capacities:
##            if temp_input in ssd_capacities[level]:
##                ssd_input = ssd_capacities[level]
##                break
##            else:
##                pass
##
##    while ram_input is None:
##        temp_input = input('RAM Capacity (GB): ').strip()
##        for level in ram_capacities:
##            if temp_input in ram_capacities[level]:
##                ram_input = ram_capacities[level]
##                break
##            else:
##                pass
##
##    search_data['keyword'] = keyword_input
##    search_data['ram'] = ram_input
##    search_data['ssd'] = ssd_input
##
##    vatan_bilgisayar.search(search_data)

def main():
    modes = {'Free Mode':freeMode} #,'2':manualMode
    mode_selection = None

    print("Which mode do you want to search with?")
    for index, mode in zip(range(1,len(modes)+1),modes):
        print(str(index)+'.',mode)
    while mode_selection not in [str(num) for num in range(1,len(modes)+1)]:
        mode_selection = input('Mode: ').strip()

    list(modes.values())[int(mode_selection)-1]()
if __name__ == "__main__":
    while True:
        main()
