
#! /usr/bin/python
# -*- coding: utf8 -*-


"""
Master Collector
----------------

1. checks list of list names
2. for each list in the list of lists
	2.1 get all available messages
	2.2 put messages into buffer
	2.3 count words
	2.4 select messages for each relevant word
	2.5 update most_recent_ids, 
3. pack everything
"""


import twitter, twython
import json, cPickle
import tokenizer
from collections import Counter
import time


# ------------------------------------------------ ------------------------------------------------>
# ------------------------------------------------>
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
	# una vez hecho el primer collect, trae mas
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

# ------------------------------------------------>
# ------------------------------------------------ ------------------------------------------------>



if __name__ == '__main__':

	do_log()
	list_of_lists =  ["mx140-ejecutivo", \
					"mx140-gobernadores", \
					"mx140-opinion", \
					"mx140-senadores", \
					"mx140-diputados", \
					"mx140-pri", \
					"mx140-pan", \
					"mx140-prd", \
					"puebla140"]

	most_recent_ids = {l:"600000000000000000" for l in list_of_lists}
	#buffers = {l:[] for l in list_of_lists}
	#cPickle.dump (buffers, open('buffers.cpk','w'))
	stopwords = [w.strip().rstrip().decode('utf8','ignore') for w in open('nsw.txt','r').readlines()]
	print stopwords
	max_buffer_size = 10000;
	max_most_common_words = 30;
	min_bag_size = 5

	while(True):
		pack_json = {}
		buffers = cPickle.load(open("buffers.cpk",'r'))
		most_recent_ids = cPickle.load(open("mrids.cpk",'r'))

		
		# fill from lists
		for l in list_of_lists:
			pack_json[l] = {}
			# get all available messages
			batch = fetch_tweets_from_list(owner_screen_name="MX_en140",\
										slug=l,\
										include_entities="false",\
										count="200",\
										since_id=most_recent_ids[l],\
										max_id="0")
			#update most_recent_ids
			try:
				most_recent_ids[l] = batch[-1]['id_str']
			except:
				most_recent_ids[l] = most_recent_ids[l]
			print "[batch]:",l,len(batch), most_recent_ids[l]
		
			#put on buffers
			new_texts = [s['text'].lower() for s in batch]
			buffers[l].extend(new_texts)
			if ( len(buffers[l])>max_buffer_size ):
				buffers[l] = buffers[l][-max_buffer_size:]
			buffers['all'].extend(new_texts)
			if ( len(buffers['all'])>max_buffer_size ):
				buffers['all'] = buffers['all'][-max_buffer_size:]
			print "[buffer]:",l,len(buffers[l]), len(new_texts)

			#count words
			C = count_words(buffers[l], stopwords)
			top_words = C.most_common(max_most_common_words)

			#select messages for each selected word
			bag = []
			for (w,c) in top_words:
				#print "\t[counts]:",l,w,c
				try:
					bag = [s for s in batch if w in s['text'].lower()]
				except:
					bag = []
					pack_json[l][w] = c#{"count": c, "bag":[]}

				#so pack only words with enough pressence
				if len(bag)>min_bag_size:
					pack_json[l][w] = c#{"count": c, "bag":bag[:min_bag_size]}
				elif len(bag)==0:
					pack_json[l][w] = c#{"count": c, "bag":[]};
				
				print "\t[bag]:",w,len(bag)
		# for the all buffer
		C = count_words(buffers['all'], stopwords)
		top_words = C.most_common(max_most_common_words)
		pack_json['all'] = {w: c for (w,c) in top_words}


		# save json
		json.dump (pack_json, open('pack.json','w'))
		cPickle.dump (buffers, open('buffers.cpk','w'))
		cPickle.dump (most_recent_ids, open('mrids.cpk','w'))
		print ("[saved]: pack.json")


		# then sleepover
		print "[sleeping]:", time.asctime()
		time.sleep(600)