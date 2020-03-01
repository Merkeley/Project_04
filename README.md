# Media Topic Tracking
# Using Natural Language Processing
# and
# Machine Learning#

The project explores the use of NLP for identifying and tracking print media 
reporting topics related to the 2020 Presidental Primaries.

We live in a culture that is hyper focused on media.  We all have social media accounts,
our current president uses twitter more than he does traditional news conferences
and the Queen of England recently hired a social media consultant.

Natural Language Processing and sentiment analysis tools have been used by online
companies for years to monitor the behavior of their customers.  However, these tools 
can also be used by media sensitive individuals and organizations.  To demonstrate
the value of these tools I chose to apply them to reporting on a current news
event - the Presidential Primary.

The foundation of any NLP project are the documents that make up the language that
will be processed.  For this project I used a news search API to identify online articles
related to the primary and then 'read' those articles into a database.  This pool
of documents makes up what is called the corpus of the NLP project.

NLP has many components but for media monitoring the first step is Topic Identification or
Topic Modeling.  After Topics are identified the corpus can be 'projected' onto those 
topics and the importance of each topic can be quantified.

This repository contains the Jupyter Notebooks and Python scripts used for this 
exploration.


The repository is arranged as follows:
    Notebooks - All jupyter notebooks for process testing and visualizations.
        Text_Prep - does initial text cleaning and storage in MongoDB collection.
        Topic_Model - compares the results of several differenty topic modeling
            techniques and creates visualizations for the best process.
        Topic_ModelTime - explores the changes in reporting topics over time.
        Topic_Model_gensim - explores using the gensim package for topic modeling.
        PCA_Clustering - explores using Principal Component Analysis combined with
            KMeans clustering for topic modeling.
        Sentiment_full_corpus - processes all articles in the corpus and assigns
            a sentiment score to the reporting.
        LocationSearch - This notebook uses Google's location search api to 
            identify the geographic locations of the publishers of the articles
            in the project corpus.

    src - Contains the source files for the Python scripts used in this project
        news_scrape.py - Contains two functions used to build the corpus.
            run_web_search - receives the handle to a search client,
                two lists of search terms and a cursor for a MongoDB collection.
                The function runs the search and stores the search results in 
                the MongoDB collection.
            scrape_news - receives a dictionary containing the information about
                an article.  The function uses this information to read the 
                article's web site, parse it and then returns the article text.
                If the site scraping fails an empty string is returned.  Because
                each news site uses a different format for their web sites I used
                a dictionary to guide parsing process to the correct tags.
