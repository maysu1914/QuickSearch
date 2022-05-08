import json
import os
import sys

from quick_search import QuickSearch

try:
    os.chdir(sys._MEIPASS)
except Exception:
    pass

if __name__ == '__main__':
    config = json.load(open('config.json'))
    print('%s %s' % (config.get('name'), config.get('version')))
    print('Copyright (c) 2021 %s.' % (config.get('author')))
    print('')
    print('Check new versions of %s from %s' % (config.get('name'), config.get('github')))
    print('')
    while True:
        qs = QuickSearch(config=config, max_page=3)
        qs.start()
        print('_________________________________\n')
