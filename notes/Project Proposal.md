# Metis Data Science Bootcamp
## San Francisco Winter 2020
## Project 4 Proposal

### Introduction

It's an election year.  Each time the election season rolls around we hear about media bias and media bubbles.  I would like to explore the content of a variety of news outlets and look for bias.

I plan to (am in the process of) scraping news articles from a large number of news outlets.  I'm using the the Azure News Search API to identify the articles related to the current 2020 Democratic candidates.  The article pages are scraped for content and the text is stored in a MongoDB Collection.  The text of the articles will then be cleaned and put into a 'bag of words' where I will attempt to use Pricipal Components Analysis to extract important features and possibly reduce the number of features.  I hope that the results of the PCA can be applied to the reduced article text and then used in a clustering algorithm to group similar articles together. 