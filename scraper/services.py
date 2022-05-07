import urllib

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options as ChromeOptions


class CustomChrome(Chrome):

    def __init__(self, *args, extensions=None, **kwargs):
        kwargs['options'] = kwargs.get('options') or ChromeOptions()
        extensions = extensions or ['driver/extensions/block_image_1_1_0_0.crx']
        kwargs['executable_path'] = kwargs.get('executable_path') or 'driver/chromedriver.exe'
        for extension in extensions:
            kwargs['options'].add_extension(extension)
        super(CustomChrome, self).__init__(*args, **kwargs)
        # self.set_window_position(-10000, 0)

    def open(self, url):
        if urllib.parse.unquote(self.current_url) != url:
            self.get(url)
