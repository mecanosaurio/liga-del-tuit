
#! /usr/bin/python
# -*- coding: utf8 -*-
"""
Hypercollector for Mx140
------------------------

	·Periodically get tweets from lists
	·Keep buffer (for each list)
	·Count words
	·Pack words and recent messages
"""


import twitter, twython
import json, cPickle
import tokenizer
from collections import Counter




def dual_login(app_data, user_data):
    """
    login, oauthdance and creates .credential file for specified user
    """
    APP_NAME = app_data['AN']
    CONSUMER_KEY = app_data['CK']
    CONSUMER_SECRET = app_data['CS']
    CREDENTIAL = '.'+user_data['UN']+'.credential'
    try:
        (oauth_token, oauth_token_secret) = twitter.oauth.read_token_file(CREDENTIAL)
        print '[Load]: %s' % CREDENTIAL
    except IOError, e:
        (oauth_token, oauth_token_secret) = twitter.oauth_dance(APP_NAME, CONSUMER_KEY, CONSUMER_SECRET)
        twitter.oauth.write_token_file(CREDENTIAL, oauth_token, oauth_token_secret)
        print '[Save:] %s' % CREDENTIAL
    api1 = twitter.Twitter(domain='api.twitter.com', api_version='1.1',
        auth=twitter.oauth.OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))
    api2 = twython.Twython(CONSUMER_KEY, CONSUMER_SECRET, oauth_token, oauth_token_secret)
    return api1, api2



def do_log(dat_file=".mx140.dat"):
    # login
    global api01, api02
    print "[APISTATE]: ",
    app_data, user_data = cPickle.load(open(dat_file,'r'))
    api01, api02 = dual_login(app_data, user_data)
    print "ok"
    return



"""
do_log();
U = api01.lists.statuses(owner_screen_name="MX_en140", \
		slug="mx140-gobernadores", \
		include_entities="false", \
		count="200", \
		since_id="613187170237440001")
"""



def fetch_tweets_from_list(owner_screen_name="MX_en140",\
			slug="mx140-opinion",\
			include_entities="false",\
			count="200",\
			since_id="600000000000000000",\
			max_id="0"):
	"""
	fetches all more recent tweets from a given list
	returns a batch list with all more recent twitter status objects
	"""
	#global very_last_id
	batch = []
	# primer collect, trata de traerlos todos
	try:
		new_statuses = api01.lists.statuses(owner_screen_name=owner_screen_name,\
											slug=slug,\
											include_entities=include_entities,\
											count=count,\
											since_id=since_id)
		if (len(new_statuses) > 2):
			batch.extend(new_statuses)
			max_id = new_statuses[-1]["id"]-1
			# update the since_id
			very_last_id = new_statuses[0]["id"]
			print "[get]:",len(new_statuses),"new statuses"
			print "\t\tfrom:", new_statuses[-1]["id"], "created at:", new_statuses[-1]["created_at"]
			print "\t\tto:", new_statuses[0]['id'], "created_at:", new_statuses[0]["created_at"]
	except:
		print "[FAIL]: max_id = ", max_id
		new_statuses = []
	# una vez hecho el primer collect, trae más
	while(len(new_statuses)>2):
		try:
			new_statuses = api01.lists.statuses(owner_screen_name=owner_screen_name, \
												slug=slug, \
												include_entities=include_entities, \
												count=count, \
												since_id=since_id, \
												max_id=max_id)
			batch.extend(new_statuses)
			max_id = new_statuses[-1]["id"]-1
			print "[get]:",len(new_statuses),"new statuses"
			print "\t\tfrom:", new_statuses[-1]["id"], "created at:", new_statuses[-1]["created_at"]
			print "\t\tto:", new_statuses[0]['id'], "created_at:", new_statuses[0]["created_at"]
		except:
			print "[FAIL]: max_id = ", max_id
			new_statuses = []
			break
	# before leave, update marks
	batch.reverse()
	return batch



#sw = [w.strip().rstrip() for w in open('nsw.txt','r').readlines()]



def count_words(texts_batch, stopwords = []):
	"""
	tokenize, count and filter stop words from a batch of texts
	return a counter or dictionary object
	"""
	tokens = []
	T = tokenizer.Tokenizer()
	# tokenize
	for text in texts_batch:
		tokens.extend(T.tokenize(text))
	# count
	C = Counter(tokens)
	# filter
	for sw in stopwords:
		if C.has_key(sw): C.pop(sw)
	for k in C.keys():
		if len(k)<4: C.pop(k)
	return C
