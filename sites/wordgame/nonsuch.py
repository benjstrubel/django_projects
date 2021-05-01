import feedparser
import random
import requests, json


def get_search_headline(searchterm):
    """ function for getting a google news rss headline based on a search term
        used for custom searches and local headlines


    :param searchterm:
    :return: text of headline
    """
    print("searching for " + searchterm)
    url = "https://news.google.com/rss?q={0}&hl=en".format(searchterm)
    print(url)
    feed = feedparser.parse(url)
    entry = feed.entries[random.randrange(0, len(feed.entries))]
    text = entry.title
    return text

def get_local_headline(ip):
    print("trying geo location for: " + ip)
    url = "http://ip-api.com/json/" + ip
    print("ip url: " + ip)
    resp = requests.get(url)
    print("response from ip-api " + str(resp.status_code))
    jsontext = json.loads(resp.content.decode())
    print("content " + resp.content.decode())
    # search for just state and country, city headlines are short and not good for mad libs
    searchterm = jsontext['regionName'] + "," + jsontext['country']
    searchterm = searchterm.replace(" ", "%20")
    return searchterm

result = get_local_headline('131.196.54.38')
print(result)
result = get_search_headline(result)
print(result)