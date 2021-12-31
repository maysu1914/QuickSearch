import string
import urllib

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
    for key in list(filter(lambda x: x, attribute_path.split('.'))):
        current_attr = current_attr.get(key)
        if not current_attr:
            return None
    else:
        return current_attr


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
