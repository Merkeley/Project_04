'''
    File: news_scrape.py

    Description:
        This script is part of a NLP project for analyzing news articles on the web.
        The functions in this file can be used to connect to an Azure news search API
        to collect the URLs of news articles.  There is a function to also scrape the 
        text of a news related page given the url.

        The data is stored in a MongoDB database.

        Each news site has a slightly different format for their page layout.  Most
        pages stored the article text in paragraph tags on their pages.  Some pages 
        use special tag/class names within other tag blocks.  A dictionary contains
        a list of special tag combinations for a few of the news sites that were
        explored in detail.  It is assumed that not all sites will be scrapable.

    Date Create: 2-15-20
    Date Modified: 2-20-20

    Update Log:

    Notes:

'''
# Import the models we will need.
import sys
import re
import os.path
import requests
import time
import pandas as pd
import json
from os import path

# Beautiful Soup and requests are used for web page parsing
from bs4 import BeautifulSoup as soup
import urllib
from urllib.request import urlopen

# Import MongoDB tools for database work
from pymongo import MongoClient
import requests

# Import required modules.
from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import SafeSearch
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.search.newssearch import NewsSearchClient

# News site definitions
div_search = { \
    'www.nytimes.com' : { 'head_tag' : ('article', 'id', 'story'),  \
        'text_tag': ('p', 'class', 'css-exrw3m')},
    'www.seattletimes.com' : {'head_tag' : ('div', 'id', 'article-content') , \
        'text_tag':('p', '', '')},
    'www.washingtonexaminer.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.msn.com' : {'head_tag' : ('div', 'id', 'maincontent') ,'text_tag':('p', '', '')},
    'www.usatoday.com' : {'head_tag' : ('article', 'class', 'gnt_pr') , \
        'text_tag':('p', 'class', 'gnt_ar_b_p')},
    'www.politico.com' : {'head_tag' : ('div', 'class', 'story-text') , \
        'text_tag':('p', 'class', 'story-text__paragraph')},
    'www.mercurynews.com' : {'head_tag' : ('div', 'class', 'body-copy') , \
        'text_tag':('p', '', '')},
    'www.wsj.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.newsweek.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.businessinsider.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.washingtonpost.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.chicagotribune.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.newyorker.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.lasvegassun.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.sfchronicle.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.latimes.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.nydailynews.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.washingtontimes.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.thenation.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.theguardian.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.foxnews.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.theatlantic.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.sfexaminer.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.bostonherald.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.thedailybeast.com' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
    'www.cnn.com' : {'head_tag' : ('', '', '') ,\
        'text_tag':('div', 'class', \
        ['zn-body__paragraph', 'zn-body__paragraph speakable'])},
    'www.denverpost.com' : {'head_tag' : ('div', 'class', 'article-body') , \
        'text_tag':('p', '', '')},
    'generic' : {'head_tag' : ('', '', '') ,'text_tag':('p', '', '')},
}

def scrape_news(article) :
    '''
        Function: scrape_news
            Given the url of a news page, attempt to scrape the text of the article.
            This function uses the div_search dictionary defined above to identify
            and special tag sequences used to store article text on specific sites.

        Arguments:
            article - MongoDB document (dictionary) what has the location information
                for the online article that we want to scrape.

    '''
    # Put the text in a list when we find it
    page_text = ''

    # Make sure we have valid data in this list
    if (article['base_url'] != '') :
        if article['base_url'] in div_search.keys() :
            # Now figure out what parts of the page we should be looking for
            paper_dict = div_search[article['base_url']]
        else :
            paper_dict = div_search['generic']


        no_head_tag = False
        soup_list = []

        # Read the response from the web site
        try :
            response = requests.get(article['url'], auth=('user', 'pass'), timeout=4)
        except :
            print('Broken pipe on : ', article['url'])
            return page_text

        # Parse the response in Beautiful Soup
        article_soup = soup(response.text, 'html5lib')

        # check the dictionary for special html tags for the article text
        if paper_dict['head_tag'][1] != '' :
            head_search_attrs = { paper_dict['head_tag'][1] : paper_dict['head_tag'][2]}
        else :
            head_search_attrs = {}

        # check the dictionary for special html tags for the article text
        if paper_dict['text_tag'][1] != '' :
            text_search_attrs = { paper_dict['text_tag'][1] : paper_dict['text_tag'][2] }
        else :
            text_search_attrs = {}



        # Find the beginning of the article text
        head_tag = None
        if paper_dict['head_tag'][0] != '' :
            head_tag = article_soup.find(paper_dict['head_tag'][0], \
                attrs = head_search_attrs)
        else :
            no_head_tag = True

        # Find all the descendants that contain the text of the article
        if head_tag != None :
            # print('Head Found')
            if text_search_attrs :
                soup_list = head_tag.find_all(paper_dict['text_tag'][0], \
                    attrs=text_search_attrs)
            else :
                soup_list = head_tag.find_all(paper_dict['text_tag'][0])

        elif (no_head_tag == True) or (head_tag == None):
            # If there is not outer grouping tag then just look for text tag
            if text_search_attrs :
                soup_list = article_soup.find_all(paper_dict['text_tag'][0], \
                    attrs=text_search_attrs)
            else :
                soup_list = article_soup.find_all(paper_dict['text_tag'][0])

        # For each block/paragraph in the document append the text
        for paragraph in soup_list :
            page_text += paragraph.text

    # return all the text that we found
    return page_text 

def run_web_search(client, candidates, other_search, mdb) :
    '''
        Function: run_web_search
            Use the news search API to find links to articles of interest

        Arguments:
            article - MongoDB document (dictionary) what has the location information
                for the online article that we want to scrape.

    '''
    # Run through each of the candidates and search for news on them
    for candidate in candidates :
        for term in other_search :
            news_list = []
            search_term = candidate + ' ' + term
            news_result = client.news.search(query=search_term, market="en-us", count=100)

            if news_result.value:
                for result in news_result.value :
                    if mdb.count_documents({'name' : result.name}) == 0 :
                        base_url = \
                            result.url[result.url.find('www.'): \
                            result.url.find('/', result.url.find('www.'))]

                        # Look to see if this article is in the list already
                        news_list.append({'name':result.name, \
                            'url': result.url.replace(' ', ''), \
                            'pub_date' : result.date_published, \
                            'provider' : result.provider[0].name, \
                            'base_url' : base_url, \
                            'scraped' : 'n' })

            if(len(news_list) > 0) :
                mdb.insert_many(news_list)


def main() :
    # Definitions needed by the search api
    subscription_key = os.environ.get('AzureAPIKey')
    endpoint = 'https://westus.api.cognitive.microsoft.com/'

    # Define our search criteria
    candidates = ['bernie sanders', 'amy klobuchar', 'joe biden', 'michael bloomberg', \
                'pete buttigieg', 'tom steyer', 'elizabeth warren']
    other_search = ['', 'campaign', 'iowa', 'new hampshire', \
            'December', 'January', 'February']

    # Define the search client
    client = NewsSearchClient(endpoint=endpoint, \
            credentials=CognitiveServicesCredentials(subscription_key))

    # Configure the database
    db_client = MongoClient()
    db_news = db_client['news_search']
    db_news_col = db_news['search_result']

    search_head = db_news_col.count_documents({})

    search_news = True
    clear_db = False
    clear_search = False

    # Check what mode we're running here
    args = sys.argv[1:]
    print(args)

    for option in args :
        print(option)
        if option == '-resume' :
            search_news = False
            clear_search = False
            clear_db = False
        elif option == '--reset' :
            search_news = True
            clear_search = True
            clear_db = True
        elif option == '-rescrape' :
            search_news = False
            clear_search = False
            clear_db = True
        else :
            print('Unknown option.  Use news_scrape [-resume | --reset]')
            return


    if clear_search == True :
        print('Resetting search database')
        db_news.drop_collection('search_result')

    if clear_db == True :
        print('Clearing database')
        db_news.drop_collection('news_content')

    if search_news == True :
        print('Searching')
        run_web_search(client, candidates, other_search, db_news_col)


    print('Starting page scraping')
    db_news_content = db_news['news_content']

    need_learn = []
    scrape_count = 0

    cursor = db_news_col.find({ 'scraped' : 'n' }, \
            {'_id':1, 'name':1, 'url':1, 'provider' : 1, 'base_url':1, 'pub_date':1})

    for article in list(cursor):
        if db_news_content.count_documents({'name' : article['name']}) == 0 : 
            article_text = scrape_news(article)
            scrape_count += 1
            if scrape_count == 100 :
                print('.')
                scrape_count = 0
 
            time.sleep(0.25)


            db_news_content.update_one({'_id':article['_id'] }, \
                { '$set' : { 'scraped' : 'y'} })
            if(len(article_text) > 0) :
                good_article = {'name' : article['name'], \
                    'url' : article['url'], 'pub_date' : article['pub_date'], \
                    'provider' : article['provider'], 'base_url' : article['base_url'], \
                    'text' : article_text}

                db_news_content.insert_one(good_article)
        else :
            need_learn.append(article['base_url'])



# Standard boilerplate to call the main() function.
if __name__ == '__main__':
  main()
