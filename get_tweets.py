from collections import Counter
import csv
import datetime
import json
import logging
import os
import re
import sys

import requests
from requests.auth import HTTPBasicAuth
from tld import get_tld
import tweepy


APP_DIR = os.path.realpath(os.path.dirname(sys.argv[0]))

# workaround for using requests with py2exe
if os.path.isfile(os.path.join(APP_DIR, 'cacert.pem')):
    os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(APP_DIR, 'cacert.pem')

with open(os.path.join(APP_DIR, 'config.json')) as f:
    config = json.load(f)

# Twitter auth
auth = tweepy.OAuthHandler(config['twitter']['consumer_key'],
                           config['twitter']['consumer_secret'])
auth.set_access_token(config['twitter']['access_token'],
                      config['twitter']['access_secret'])
api = tweepy.API(auth)

# create some empty lists
links = []
domains = []
firstpass = []
topics = []
tags = []

# make variables for the two Alchemy APIs I want to use
ConceptsAPI = "https://gateway.watsonplatform.net/natural-language-understanding/api/v1/analyze?version=2017-02-27"

# make a variable for the Twitter usernames file by reading the text
# file usernames.txt
with open('usernames.txt', 'r+') as f:
    usernames = f.read().splitlines()


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config['log_level']))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Stream handler
    stream_hdlr = logging.StreamHandler()
    stream_hdlr.setFormatter(formatter)
    logger.addHandler(stream_hdlr)

    # Setup logging to file
    file_hdlr = logging.FileHandler('get_tweets.log')
    file_hdlr.setFormatter(formatter)
    logger.addHandler(file_hdlr)

    return logger


logger = get_logger(__name__)


def CountDomains(usernames):

    logger.info("Starting tweet collection...")
    logger.info(str(len(usernames)) + " usernames.")

    session = requests.Session()

    # for all the usernames in the usernames file...
    for name in usernames:
        logger.info('Getting timeline for %s' % name)
        try:
            # create a variable named public_tweets
            public_tweets = api.user_timeline(name, count=20)
        except Exception:
            logger.exception("Error getting timeline for %s" % name)
            continue
        # for every tweet in the public_tweets list...
        for tweet in public_tweets:

            # use regex to find the links in the tweet body
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet.text)

            # for every url in the list of urls that the regex found
            for url in urls:
                try:
                    # request each link using the requests library
                    # follow redirects.
                    link = session.get(url, allow_redirects=True).url
                    # put all of the urls into the list named links
                    links.append(link)
                    # use the get_tld function from the tld library
                    domain = get_tld(link)
                    # append the domain to the domains list
                    domains.append(domain)
                except:
                    logger.exception('Trouble determining top level domain for %s' % url)
                    pass

        logger.info("Finished: " + name)

    logger.info("Starting Watson analysis of links...")
    logger.info(str(len(links)) + " links.")

    # for each of the urls in the urls list that was created above...
    session.auth = HTTPBasicAuth(config['watson']['username'],
                                 config['watson']['password'])
    for link in links:
        # create a new url by concatenating the concepts API base url
        # (defined at the start) to the link we want to get the concepts for
        payload = {
            "url": link,
            "features": {
                "concepts": {
                    "limit": config['watson']['limit']
                }
            }
        }

        logger.debug('Sending %s to watson for analysis' % link)
        # create a variable named r which is the content from the API request
        r = session.post(ConceptsAPI, json=payload)

        if r.status_code != 200:
            logger.warning("ConceptsAPI returned %s: %s for %s" % (r.status_code, r.text, link))
            continue

        for concept in r.json()["concepts"]:
            tags.append(concept["text"])
        logger.info("Finished: " + link)

    logger.info("Done. :)")

    today = datetime.datetime.now()
    postfix = today.strftime('%Y-%m-%d-%H-%M')

    with open("domains_" + postfix + ".csv", "wb") as personas:
        personaswriter = csv.writer(personas)
        for domain, count in dict(Counter(domains)).items():
            personaswriter.writerow([domain, count])

    with open("concepts_" + postfix + ".csv", "wb") as concepts:
        conceptswriter = csv.writer(concepts)
        for tag, count in dict(Counter(tags)).items():
            conceptswriter.writerow([tag, count])

CountDomains(usernames)
