import concurrent
import string
import time
import urllib
from concurrent.futures import ThreadPoolExecutor
from ssl import SSLError

import requests
from requests.models import PreparedRequest
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options as ChromeOptions


class CustomWebDriver(Chrome):
    def open(self, url):
        if urllib.parse.unquote(self.current_url) != url:
            self.get(url)


def get_driver():
    extensions = ['driver/extensions/block_image_1_1_0_0.crx']
    options = ChromeOptions()
    # options.headless = True
    # options.add_argument("--start-maximized")
    for extension in extensions:
        options.add_extension(extension)
    driver = CustomWebDriver(executable_path="driver/chromedriver.exe", options=options)
    driver.set_window_position(-10000, 0)
    return driver


def prepare_url(url, params):
    """
    it will prepare an url with query strings by given params
    """
    req = PreparedRequest()
    req.prepare_url(url, params)
    return req.url


def get_attribute_by_path(dictionary, attribute_path):
    current_attr = dictionary
    for key in attribute_path.split('.'):
        current_attr = current_attr.get(key)
        if not current_attr:
            return None
    else:
        return current_attr


def get_page_contents(url_list):
    threads = []
    for index, url in enumerate(url_list):
        threads.append(ThreadPoolExecutor().submit(get_page_content, url))
        if index > 1 and index % 20 == 0:
            time.sleep(5)
        else:
            time.sleep(0.2)
    for thread in concurrent.futures.as_completed(threads):
        yield thread.result()


def get_page_content(url, counter=3, dynamic_verification=True):
    """
    Content retriever
    :param dynamic_verification: try without SSL verify if needed
    :param url: the link whose content is to be returned
    :param counter: how many times of retrying
    :return: content of response
    """
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }
    verify = True
    for count in range(1, counter + 1):
        try:
            return requests.get(url, timeout=10, headers=headers, verify=verify).content
        except Exception as e:
            print('Error occurred while getting page content!', count, url, e)
            verify = False if dynamic_verification and type(e) == SSLError else True
    return ''


def get_text(element):
    """
    it will parse the text of element without children's
    returns the whole texts if no text found
    """
    text = ''.join(element.find_all(text=True, recursive=False)).strip()
    return text if text else element.text


def is_formattable(text):
    return any([tup[1] for tup in string.Formatter().parse(text) if tup[1] is not None])


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start
