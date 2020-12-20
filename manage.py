import multiprocessing

from QuickSearch.QuickSearch import QuickSearch

if __name__ == '__main__':
    while True:
        multiprocessing.freeze_support()
        qs = QuickSearch(max_page=1)
        qs.search()
