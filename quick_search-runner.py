import json
import logging
import os
import sys
from datetime import datetime

from quick_search import QuickSearch

try:
    os.chdir(sys._MEIPASS)
except Exception:
    pass

if __name__ == '__main__':
    os.path.exists('logs') or os.mkdir('logs')
    print("""Logs path: "%s"\n""" % os.path.abspath("logs"))
    logging.basicConfig(
        filename='logs/%s.log' % datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f'),
        format='[%(asctime)s] - %(levelname)s\t- %(message)s',
        encoding='utf-8',
        level=logging.DEBUG
    )
    config = json.load(open('config.json'))
    while True:
        qs = QuickSearch(config=config, max_page=3)
        qs.start()
        print('_________________________________\n')
