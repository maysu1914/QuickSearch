from QuickSearch.QuickSearch import QuickSearch

if __name__ == '__main__':
    print("QuickSearch v0.9.41")
    print("Copyright (c) 2020 maysu1914.")
    print("")
    print("Check new versions of QuickSearch from https://github.com/maysu1914/QuickSearch")
    print("")

    while True:
        qs = QuickSearch(max_page=1)
        qs.search()
