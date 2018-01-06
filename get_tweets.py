from collections import Counter
import csv
import datetime
import json
import os
import re
import sys

import requests
from requests.auth import HTTPBasicAuth
from tld import get_tld
import tweepy


APP_DIR = os.path.realpath(os.path.dirname(sys.argv[0]))

try:
    with open(os.path.join(APP_DIR, 'config.json')) as f:
        config = json.load(f)
except IOError:
    sys.exit('Copy config.example.json and save as config.json')

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
try:
    with open('usernames.txt', 'r+') as f:
        usernames = f.read().splitlines()
except IOError:
    sys.exit('usernames.txt not found.')


def CountDomains(usernames):

    print "Starting tweet collection..."
    print str(len(usernames)) + " usernames.\n"

    session = requests.Session()

    # for all the usernames in the usernames file...
    for name in usernames:
        try:
            # create a variable named public_tweets
            public_tweets = api.user_timeline(name, count=20)
        except Exception as ex:
            print "Error getting timeline for %s: %s" % (name, ex.message)
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
                    pass

        print "\tFinished: " + name

    print "\nStarting Watson analysis of links..."
    print str(len(links)) + " links.\n"

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

        # create a variable named r which is the content from the API request
        r = session.post(ConceptsAPI, json=payload)

        if r.status_code != 200:
            print "\nConceptsAPI returned %s: %s for %s" % (r.status_code, r.text, link)
            continue

        for concept in r.json()["concepts"]:
            tags.append(concept["text"])
        print "\tFinished: " + link

    print "\nDone. :)"

    today = datetime.datetime.now()
    postfix = today.strftime('%Y-%m-%d-%H-%M')

    with open("domains_" + postfix + ".csv", "a") as personas:
        personaswriter = csv.writer(personas)
        for domain, count in dict(Counter(domains)).items():
            personaswriter.writerow([domain, count])
        personas.close()

    with open("concepts_" + postfix + ".csv", "a") as concepts:
        conceptswriter = csv.writer(concepts)
        for tag, count in dict(Counter(tags)).items():
            conceptswriter.writerow([tag, count])
        concepts.close()

CountDomains(usernames)
