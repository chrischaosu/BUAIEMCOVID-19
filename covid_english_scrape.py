import collections
import os
import numpy as np
import pandas as pd
import re
import string

from newspaper import Article
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer


content_full = []
# nltk.download('stopwords')
# nltk.download('wordnet')
stopwords = stopwords.words('english')
stopwords = stopwords + ['coronavirus', 'covid', 'corona']
lemmatizer = WordNetLemmatizer()
universal_count = collections.Counter()
dfs = []

# ^^ Here we're just importing libraries and instantiating some global variables.
dont_stem = {'Sanders'}
special_words = [
'donald trump',
'white house',
'social distancing',
'stock market',
'new york',
'joe biden',
'bernie sanders',
'world health organization',
'face mask',
'mike pence',
'vice president',
'hong kong',
'united states',
'diamond princess',
'new hampshire',
'whats happening',
'lunar year',
'los angeles',
'san francisco',
'elissa slotkin']

urls_mainstream = [
    'nytimes.com',
    'washingtonpost.com',
    'usatoday.com',
    'wsj.com',
    'newsweek.com',
    'nbcnews.com',
    'cbsnews.com',
    'abcnews.go.com',
    'cnn.com',
    'pbs.org',
    'npr.org',
    'latimes.com',
    'chicagotribune.com'
]

urls_conservative = [
    'foxnews.com',
    'breitbart.com',
    'newsmax.com',
    'theblaze.com',
    'dailycaller.com',
    'drudgereport.com'
]

urls_liberal = [
    'msnbc.com',
    'motherjones.com',
    'theatlantic.com',
    'huffingtonpost.com',
    'vox.com',
    'slate.com',
    'buzzfeednews.com',
    'dailykos.com'
]

def get_category_of_news_outlet(url):
    for url_m in urls_mainstream:
        if url_m in url:
            return 'mainstream'
    for url_c in urls_conservative:
        if url_c in url:
            return 'conservative'
    for url_l in urls_liberal:
        if url_l in url:
            return 'liberal'
    return None

def substitute_special_words(content):
    content = content.translate(str.maketrans('', '', ''.join(punctuation_no_underscore) + string.digits))
    content = content.lower()
    for w in special_words:
        if w in content:
            content = re.sub(w,  '_'.join(w.split()), content)
            
    return content

punctuation_no_underscore = set(string.punctuation)
punctuation_no_underscore.add('’')
punctuation_no_underscore.add('”')
punctuation_no_underscore.remove('_')

docs_location = '../Downloads/cv_us_20191201_to_20200320/'

# here we go through a directory containing all the Excel spreadsheets
for doc in os.listdir(docs_location):
    print(doc)
    df = pd.read_excel(os.path.join(docs_location + doc))
    # pd.read_excel seems to want to grab the header line, so we make sure to ignore that; 
    # column 'Unnamed: 3' is the actual article content.
    content_scraped = []
    count_scraped = 0
    for url, headline in zip(df['Unnamed: 2'][1:], df['Unnamed: 3'][1:]):
        try:
            article = Article(url)
            article.download()
            article.parse()
            text = article.text  # this is getting the text
            content_scraped.append(text)
        except Exception as e:
            print(e)
            content_scraped.append(headline)
        if count_scraped % 10 == 0:
            print(float(count_scraped / len(df)))
        count_scraped += 1
    content_not_clean_yet = content_scraped
    # we remove punctuation here
    content_not_clean_yet = [substitute_special_words(c) for c in content_not_clean_yet]
    content_no_punctuation = [[word for word in c.split() if re.match('[a-zA-Z0-9]+', word)] for c in content_not_clean_yet]
    # here we remove stopwords
    content_no_stopwords = [
        [c for c in content if c not in stopwords]
        for content in content_no_punctuation
        
    ]
    # I'm using gensim's native lemmatizer to lemmatize our content
    content_lemmatized = [
        [lemmatizer.lemmatize(c) for c in content \
         if c != 'sanders' and c not in special_words] 
    for content in content_no_stopwords]
    # here we get rid of short words
    content_full = [[c for c in content if len(c) > 2] for content in content_lemmatized]
    # get dates (splitting up by week of year)
    # the timedelta is necessary to align so that Sunday is the first day of the week.
    dates_full = list(df['Unnamed: 1'][1:].apply(lambda b: pd.to_datetime(b + pd.Timedelta(days=1)).week))
    # and get string dates so we can confirm we're getting correct weeks
    str_times = list(df['Unnamed: 1'][1:].apply(lambda b: pd.to_datetime(b).strftime('%Y%m%d')))
    df = df[1:]
    df['dates_full'] = dates_full
    df['content_full'] = content_full
    df['dt_str'] = str_times
    df['political_leaning'] = df['Unnamed: 2'].apply(get_category_of_news_outlet)
    df.to_csv(doc[:-4] + '_news_full.csv')
    dfs.append(df)
    
# df_final contains all data.
df_final = pd.concat(dfs)
df_final.to_csv('full_text_us_coronavirus_news.csv')
