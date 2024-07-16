from urllib.parse import unquote

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium_stealth import stealth


class CustomChrome(Chrome):

    def __init__(self, *args, extensions=None, **kwargs):
        kwargs['options'] = kwargs.get('options') or ChromeOptions()
        for extension in extensions or []:
            kwargs['options'].add_extension(extension)
        super(CustomChrome, self).__init__(*args, **kwargs)
        stealth(self,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        # self.set_window_position(-10000, 0)

    def open(self, url):
        if unquote(self.current_url) != url:
            self.get(url)
