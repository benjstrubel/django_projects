import os
import random
import time
import logging
import feedparser
import requests
from scipy.spatial.distance import cosine
import json
import datetime
import pyttsx3
from .constants import Constants
from .models import Blurb

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    }
})
logger = logging.getLogger(__name__)

class PreferenceServices:
    INCREMENT = .2  # pref increment factor

    def __init__(self):
        pass

    def record_vote(self, session_pref_vec, category, vote):
        logger.debug("before vote: " + str(session_pref_vec))
        if vote == "1":
            logger.info("like vote")
            self.like(session_pref_vec,category)
        elif vote == "0":
            logger.info("DISlike vote")
            self.dislike(session_pref_vec,category)
        logger.debug("after vote: " + str(session_pref_vec))
        return session_pref_vec


    def like(self,session_pref_vec, category):
        session_pref_vec.prefs[category] += self.INCREMENT
        if session_pref_vec.prefs[category] > 1:
            session_pref_vec.prefs[category] = 1

    def dislike(self, session_pref_vec, category):
        session_pref_vec.prefs[category] -= self.INCREMENT
        if session_pref_vec.prefs[category] < 0:
            session_pref_vec.prefs[category] = 0


#class for voice/text manipulation
class LanguageServices:
    #text to speech function
    def text_to_speech(self, text, sessionid):
        fullfilepath = "/home/ubuntu/tempaudio/" + sessionid + '.mp3'
        engine = pyttsx3.init()
        engine.setProperty('volume', 1)
        engine.setProperty('rate', 140)
        engine.setProperty('voice', 'english-north')
        #library only saves to disk, extra I/O for no reason :(
        engine.save_to_file(text, fullfilepath)
        logger.info("saving to file running and waiting...")
        engine.runAndWait()

        #wait for file to be created, not sure why django runs runAndWait async
        wait_time = 7
        counter = 0
        while not os.path.exists(fullfilepath):
            time.sleep(1)
            counter += 1
            if counter > wait_time:
                break
        try:
            with open(fullfilepath, "rb") as f:
                bytes = f.read()
            logger.info("file found and read")
            #remove file
            os.remove(fullfilepath)
        except Exception as e:
            logger.error("file not found",e)
            bytes = None #set as none, handled by views
        return bytes

    #convert speech to text using azure cognition svcs
    def speech_to_text(self, bytes):
        logger.info("trying speech to text")
        url = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US"
        headers = {
            'Ocp-Apim-Subscription-Key': 'redacted',
            'Content-type': 'audio/wav'
        }
        resp = requests.post(url, headers=headers, data=bytes)
        logger.debug("got resp from azure:",resp)
        guess = json.loads(resp.content.decode())
        logger.info("guess is:",guess["DisplayText"])
        return guess["DisplayText"]


#class for handlign current headlines
class CurrentHeadlineServices:
    #function to get a local headline based on user ip via ip-api.com
    def get_local_headline(self, ip):
        try:
            logger.info("trying geo location for: ", ip)
            url = "http://ip-api.com/json/" + ip
            resp = requests.get(url)
            logger.debug("response from ip-api",resp)
            jsontext = json.loads(resp.content.decode())
            #search for just state and country, city headlines are short and not good for mad libs
            searchterm = jsontext['regionName'] + "," + jsontext['country']
            searchterm = searchterm.replace(" ","")
            text = self.get_search_headline(searchterm)
        except Exception as e:
            logger.error("error getting ip location",e)
            text = "-1"
        return text

    #function for getting a google news rss headlien based on a searhc term
    #used for custom searches and local headlines
    def get_search_headline(self, searchterm):
        url = "https://news.google.com/rss?q={0}&hl=en".format(searchterm)
        feed = feedparser.parse(url)
        entry = feed.entries[random.randrange(0, len(feed.entries))]
        text = entry.title
        return text

    #get a current headline
    def get_current_headline(self, category):
        logger.info("getting current headline for " + category)
        #pref category to url dictionary
        urls = {
            "entertainment" : "http://rss.cnn.com/rss/cnn_showbiz.rss",
            "health" : "http://rss.cnn.com/rss/cnn_health.rss",
            "politics" : "http://rss.cnn.com/rss/cnn_allpolitics.rss",
            "sports" : "https://www.cbssports.com/rss/headlines/",
            "technology" : "http://rss.cnn.com/rss/cnn_tech.rss",
            "business" : "http://rss.cnn.com/rss/money_latest.rss",
            "travel" : "http://rss.cnn.com/rss/cnn_travel.rss"
        }
        feed = feedparser.parse(urls[category])
        entry = feed.entries[random.randrange(0,len(feed.entries))]
        text = entry.title + ". " + entry.summary.split("<div")[0] + "."
        return text

#class for dealing with django blurb models
class BlurbServices:

    def get_highest_cat(self, blurb):
        scorevectors = blurb.scorevectornew
        #get highest cat
        max_category = (Constants.CATEGORY_DEFAULT,0)
        for a_scorevector in scorevectors:
            if a_scorevector.score > max_category[1]:
                max_category = (a_scorevector.category,a_scorevector.score)
        return max_category[0]

    def get_blurbs_scores_as_dict(self,id):
        blurb = Blurb.objects.get(id=id)
        scores = blurb.scorevectornew_set.all()
        dict = {score.category:score.score for score in scores}
        return dict

    def get_blurb(self,prefvector_obj):
        logger.info("finding blurb for this prefector:", prefvector_obj)
        #get user prefers as vector
        user_vec = prefvector_obj.get_as_vec_order_by_cat()
        #store pk_id:cosine_sim_score
        sim_scores = {}

        #calc all cosine sim scores
        for blurb in Blurb.objects.all():
            #initiliaze blank dictionary with correct order
            blurb_scores = {key : 0 for key in Constants.CATEGORIES}
            scores_list = blurb.scorevectornew_set.all()
            for score in scores_list:
                blurb_scores[score.category] = score.score
            #convert to vector
            blurb_vec = [v for v in blurb_scores.values()]
            cosine_sim_score = 1 - cosine(user_vec,blurb_vec)
            sim_scores[blurb.pk] = cosine_sim_score

        #order by cosine sim scores and get random high score
        sorted_sim_scores = sorted(sim_scores.items(),key=lambda x: x[1],reverse=True)
        #
        max = Constants.MAX_BLURBS_TO_CHOOSE_FROM if len(sorted_sim_scores) > Constants.MAX_BLURBS_TO_CHOOSE_FROM else len(sorted_sim_scores)
        logger.debug("max blurbs is: ", max)
        idx = random.randrange(0,max)
        logger.debug("random index is: ", idx)
        pk = sorted_sim_scores[idx][0]

        blurb = Blurb.objects.get(pk=pk)
        return blurb

    #process blurb by tagging pos
    def process_blurb(self, blurb):
        #nlp text
        nlp = NLPServices()
        jsontext = nlp.tag_blurb(blurb.text)
        return jsontext

#class for communicating with nlp server
class NLPServices:
    #function to classify and unknown headline
    #used for local, current, and custom headlines
    def classify_headline(self,text):
        data = json.dumps({'text':text})
        text_score_vector = self.send_and_recv_msg('/classify',data)
        return text_score_vector

    #tag the POS in a blurb
    def tag_blurb(self,text):
        data = json.dumps({'text' : text})
        tagged_blurb = self.send_and_recv_msg('/tag',data)
        return tagged_blurb

    def send_and_recv_msg(self, path, data):
        root_url = 'http://127.0.0.1:5000/'
        headers = {'Content-type':'application/json','Accept':'text/plain'}

        url = root_url + path
        r = requests.post(url,headers=headers,json=data)
        if(r.status_code == 200):
            try:
                resp = r.json()
                return resp
            except:
                logger.error("error parsing server response")
        else:
            logger.error("non 200 status code " + str(r.status_code))
        return {}

    #main function to prepare a blurb to be rendered by views
    def prep_blurb(self, json_text):
        logger.debug("prepping blurb...")
        WORD_REPLACE_COUNT = 3 #replace 3 words
        for x in range(0,WORD_REPLACE_COUNT):
            json_text = self.replace_pos(json_text)
        logger.info("text with removed words will be " + str(json_text))
        return json_text

    def replace_pos(self,json_text):
        logger.debug('replacing pos...')
        MAXLOOPTIME = 1
        PTB_TO_ENGLISH = {
            'JJ' : 'Adjective',
            'JJR' : 'Comparative Adjective',
            'JJS' : 'Superlative Adjective',
            'NN' : 'Singular Noun',
            'NNS' : 'Plural Noun',
            'NNP' : 'Singular Proper Noun',
            'NNPS' : 'Plural Proper Noun',
            'RB' : 'Adverb',
            'RBR' : 'Comparative Adverb',
            'RBS' : 'Superlative Adverb',
            'VB' : 'Verb, Base Form',
            'VBD' : 'Verb, Past Tense',
            'VBG' : 'Verb, Gerund or Present Participle',
            'VBN' : 'Verb, Past Participle',
            'VBP' : 'Verb, Non 3rd Person Singular Present',
            'VBZ' : 'Verb, 3rd Person Singular Present',
            'CD' : 'Number'
        }
        max = len(json_text['words'])-1

        notdone = True
        time = datetime.datetime.now().timestamp()

        while(notdone):
            idx = random.randrange(0,max)
            #only replace certain tags
            if(json_text['pos'][idx] in PTB_TO_ENGLISH.keys() and json_text['words'][idx] != "%%%"):
                json_text['words'][idx] = "%%%"
                json_text['pos'][idx] = PTB_TO_ENGLISH[json_text['pos'][idx]] #make spacy upos readable by users
                notdone = False
            if datetime.datetime.now().timestamp()-time > MAXLOOPTIME:
                logger.error('max loop time exceeded')
                notdone = False

        return json_text