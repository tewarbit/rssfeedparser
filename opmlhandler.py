import logging
import feedparser
import urllib
import urllib2
from xml.dom import minidom
from time import mktime


BASE_URL = "http://localhost:8001/util/"
CREATE_FEED = "create_feed_item"
CREATE_SUBSCRIPTION = "create_subscription"

TRANSLATIONS = [(u'\u2019', '\''), 
                (u'\u2018', '\''), 
                (u'\u2013', '-'), 
                (u'\u201D', '"'), 
                (u'\u201C', '"')]


class OpmlHandler:
  
  def __init__(self, feed):
    self.opml = minidom.parseString(feed)

  
  def process(self, userid):
    feeds = self.opml.getElementsByTagName('outline')
    for feed in feeds: 
      self.process_feed(feed, userid)

    logging.info("Completed processing of opml file!")


  def process_feed(self, feed, userid):
    feedurl = feed.getAttribute("xmlUrl")
    logging.info("Parsing the feed: %s" % feedurl)
    rssfeed = feedparser.parse(feedurl)

    logging.info("Found %d entries. Processing..." % len(rssfeed.entries))

    subscription_name = self.do_latin1_translate(rssfeed.feed.title)
    for entry in rssfeed.entries:
      self.process_entry(entry, subscription_name, userid)


    payload = urllib.urlencode({'name': subscription_name, 'userid': userid})

    logging.info("Posting to rsstrackerd (create subscription)")
    results = urllib2.urlopen(BASE_URL + CREATE_SUBSCRIPTION, payload)
    logging.info("Received response: %d" % results.getcode())
    
    logging.info("Completed processing of feed: %s !" % subscription_name)

  
  def process_entry(self, entry, subscription_name, userid):
    item_title = self.do_latin1_translate(entry.title)
    item_content = self.get_entry_content(entry)
    item_date = self.get_entry_date(entry)
    item_author = self.get_entry_author(entry)
    item_link = entry.link

    payload = urllib.urlencode({'subscriptionname': subscription_name, 'itemname': item_title, 'content': item_content,
                                'date': item_date, 'author': item_author, 'link': item_link, 'userid': userid})

    logging.info("Posting to rsstrackerd (create feed item)")
    results = urllib2.urlopen(BASE_URL + CREATE_FEED, payload)
    logging.info("Received response: %d" % results.getcode())

  
  def get_entry_content(self, entry):
    if 'content' in entry:
      return self.do_latin1_translate(entry.content[0].value)
    elif 'summary_detail' in entry:
      return self.do_latin1_translate(entry.summary_detail.value)
    elif 'summary' in entry:
      return self.do_latin1_translate(entry.summary)

    logging.error("Unable to find any content in entry: %s" % str(entry))
    return None


  def get_entry_date(self, entry):
    parsed_time = None

    if 'published_parsed' in entry:
      parsed_time = entry.published_parsed
    elif 'updated_parsed' in entry:
      parsed_time = entry.updated_parsed
    else:
      return None

    return mktime(parsed_time)


  def get_entry_author(self, entry):
    if 'author' in entry:
      return self.do_latin1_translate(entry.author)

    return None


  def do_latin1_translate(self, s):
    for translate in TRANSLATIONS:
      s = s.replace(translate[0], translate[1])

    return s.encode('iso-8859-1', 'replace')

