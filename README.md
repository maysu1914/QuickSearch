# quick_search
A project based on Python to make product searching on internet much easier and quicker. Searching every website regularly for a product may tire the user, with this project you can search your product or products very easy and quick.

## Requirements
Install requirements by typing "pip3 install -r requirements.txt" your terminal in the base folder

## Executable Creation
    pyinstaller --onefile --add-data "config.json;." quick_search-runner.py

## Special search style
You can search your products with this special search style:

**Standart searching**

    input:
    asus notebook
    
    searches to be made: 
    asus notebook

**Special Searching Example 1**

    input:
    [asus notebook, acer notebook]
    
    searches to be made:
    asus notebook
    acer notebook

**Special Searching Example 2**

    input:
    [asus, acer] notebook
    
    searches to be made:
    asus notebook
    acer notebook

**Special Searching Example 3**

    input:
    [asus, acer] [8gb ram, 16gb ram] windows
    
    searches to be made:
    asus 8gb ram windows
    asus 16gb ram windows
    acer 8gb ram windows
    acer 16gb ram windows

You can use this style when you are not searching for a particular product. Of course, it will take some time to search because of many requests to be made. You can calculate the minimum number of requests to be made by multiplying the number of words in the word lists with each other and multiplying that number with the number of websites to search.

*For example, there is minimum of 2x2 requests will be made for each website in the third example*
