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
        level=logging.INFO
    )
    config = json.load(open('config.json', encoding="utf-8"))


    def my_handler(type, value, tb):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.exception("Uncaught exception: {},{},{}".format(
            exc_type, fname, exc_tb.tb_lineno
        ))


    # Install exception handler
    sys.excepthook = my_handler
    while True:
        qs = QuickSearch(config=config, max_page=3)
        qs.start()
        print('_________________________________\n')
