import os
import random
import time
import feedparser
import requests
from scipy.spatial.distance import cosine
import socket
import struct
import json
import datetime
import pyttsx3
from .models import Blurb

#utlity class w/ static functions for manipulating preference vector
class PrefVector:
    INCREMENT = .2 #pref increment factor

    #record user vote
    @staticmethod
    def record_vote(prefvector, category, vote):
        #record vote
        if vote == "1":
            print("voting 1...")
            prefvector = PrefVector.like(prefvector, category)
        elif vote == "0":
            print("voting 0...")
            prefvector = PrefVector.dislike(prefvector, category)
        return prefvector

    #record a like vote
    @staticmethod
    def like(pv, category):
        pv[category] += PrefVector.INCREMENT
        if pv[category] > 1:
            pv[category] = 1
        return pv

    #record dislike
    @staticmethod
    def dislike(pv, category):
        pv[category] -= PrefVector.INCREMENT
        if pv[category] < 0:
            pv[category] = 0
        return pv

    #convert internal dict to numeric vector
    @staticmethod
    def get_as_vector(prefvector):
        #hardcoding to make sure order is correct
        v = list()
        v.append(prefvector['entertainment'])
        v.append(prefvector['health'])
        v.append(prefvector['politics'])
        v.append(prefvector['sports'])
        v.append(prefvector['tech'])
        return v

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
        print("saving to file running and waiting...")
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
            print("file found and read")
            #remove file
            os.remove(fullfilepath)
        except Exception as e:
            print("file not found")
            print(e)
            bytes = None #set as none, handled by views
        return bytes

    #convert speech to text using azure cognition svcs
    def speech_to_text(self, bytes):
        print("trying speech to text")
        url = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US"
        headers = {
            'Ocp-Apim-Subscription-Key': 'redacted',
            'Content-type': 'audio/wav'
        }
        resp = requests.post(url, headers=headers, data=bytes)
        print("got resp from azure:",resp)
        guess = json.loads(resp.content.decode())
        print("guess is:",guess["DisplayText"])
        return guess["DisplayText"]


#class for handlign current headlines
class CurrentHeadlineServices:
    #function to get a local headline based on user ip via ip-api.com
    def get_local_headline(self, ip):
        try:
            print("trying geo location for: ", ip)
            url = "http://ip-api.com/json/" + ip
            resp = requests.get(url)
            print("response from ip-api",resp)
            jsontext = json.loads(resp.content.decode())
            #search for just state and country, city headlines are short and not good for mad libs
            searchterm = jsontext['regionName'] + "," + jsontext['country']
            searchterm = searchterm.replace(" ","")
            text = self.get_search_headline(searchterm)
        except Exception as e:
            print("error getting ip location")
            print(e)
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
        #pref category to url dictionary
        urls = {
            "entertainment" : "http://rss.cnn.com/rss/cnn_showbiz.rss",
            "health" : "http://rss.cnn.com/rss/cnn_health.rss",
            "politics" : "http://rss.cnn.com/rss/cnn_allpolitics.rss",
            "sports" : "https://www.cbssports.com/rss/headlines/",
            "tech" : "http://rss.cnn.com/rss/cnn_tech.rss"
        }
        feed = feedparser.parse(urls[category])
        entry = feed.entries[random.randrange(0,len(feed.entries))]
        text = entry.title + ". " + entry.summary.split("<div")[0] + "."
        return text

#class for dealing with django blurb models
class BlurbServices:

    #get highest category for blurb
    def get_highest_cat(self, blurb):
        sv = blurb.scorevector
        #horrible code :( needs to be optimized
        vect = [sv.entertainment_score,sv.health_score,sv.politics_score,sv.sports_score,sv.tech_score]
        print("finding max cat for this blurb vector:", vect)
        cats = ["entertainment","health","politics","sports","tech"]
        maxcat = cats[vect.index(max(vect))]
        print("max cat is:",maxcat)
        return maxcat

    #get a blurb from the db based on user preference
    def get_blurb(self, prefvector):
        MAX_BLURBS = 6 #max results to choose random blurb from
        print("finding blurb for this prefector:",prefvector)
        #store pk_id:cosine_sim_score
        sim_scores = {}

        #calc all cosine sim scores
        #TODO: rewrite to use heap to avoid sorting entire set at end?
        for blurb in Blurb.objects.all():
            sv = blurb.scorevector
            blurb_vector = [sv.entertainment_score,sv.health_score,sv.politics_score,sv.sports_score,sv.tech_score]
            cosine_sim_score = 1 - cosine(prefvector,blurb_vector)
            sim_scores[blurb.pk] = cosine_sim_score

        #order by cosine sim scores and get random high score
        sorted_sim_scores = sorted(sim_scores.items(),key=lambda x: x[1],reverse=True)
        #
        max = MAX_BLURBS if len(sorted_sim_scores) > MAX_BLURBS else len(sorted_sim_scores)
        print("max blurbs is: ", max)
        idx = random.randrange(0,max)
        print("random index is: ", idx)
        #pk = next(iter(sorted_sim_scores))[0]
        pk = sorted_sim_scores[idx][0]

        blurb = Blurb.objects.get(pk=pk)
        return blurb

    #process blurb by tagging pos
    def process_blurb(self, blurb):
        #nlp text
        nlp = NLPServices()
        jsontext = nlp.tag_blurb(blurb.text)
        return jsontext

#django to nlp server message class
#static methods to create and decode messages
class Message:
    @staticmethod
    def encode_msg_size(int_size):
        return struct.pack("<I", int_size)

    @staticmethod
    def decode_msg_size(size_bytes):
        return struct.unpack("<I", size_bytes)[0]

    @staticmethod
    def create_msg(content_bytes):
        size = len(content_bytes)
        return Message.encode_msg_size(size) + content_bytes

#class for communicating with nlp server
class NLPServices:
    #function to classify and unknown headline
    #used for local, current, and custom headlines
    def classify_headline(self, text):
        dict = {
            "cmd" : "classify",
            "payload" : text
        }
        msg = json.dumps(dict)
        text_score_vector = self.send_and_recv_msg(msg)
        return json.loads(text_score_vector)

    #tag the POS in a blurb
    def tag_blurb(self, text):
        dict = {
            "cmd" : "postag",
            "payload" : text
        }
        msg = json.dumps(dict)
        tagged_blurb = self.send_and_recv_msg(msg)
        return json.loads(tagged_blurb)

    #send message to nlp server and read response
    def send_and_recv_msg(self, text):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('127.0.0.1', 9999)

        sock.connect(server_address)
        mymsg = Message.create_msg(text.encode())
        sock.sendall(mymsg)
        #until it can be fixed this infuriating line is needed in order to raise the underlying "buffer available to be read" flag on the server
        sock.shutdown(socket.SHUT_WR)
        print("send finished")

        msglen = sock.recv(4)
        msglen = Message.decode_msg_size(msglen)
        print("got msg len as: " + str(msglen))
        msg = b''
        while len(msg) < msglen:
            msg += sock.recv(2048)
        msg = msg.decode()
        print("text is: " + msg)
        return msg

    #main function to prepare a blurb to be rendered by views
    def prep_blurb(self, json_text):
        WORD_REPLACE_COUNT = 3 #replace 3 words
        for x in range(0,WORD_REPLACE_COUNT):
            json_text = self.replace_pos(json_text)
        return json_text

    #replace one valid POS with placehodler symbol for user input
    def replace_pos(self,json_text):
        MAXLOOPTIME = 2 #limit loop to 2 seconds to prevent infinite loop
        VALID_TAGS = ['NOUN', 'VERB', 'PROPN', 'ADV', 'ADJ', 'NUM']
        UPOS_TO_ENGLISH = {
            "NOUN": "Noun",
            "ADV": "Adverb",
            "ADJ": "Adjective",
            "PROPN": "Proper Noun",
            "VERB": "Verb",
            "NUM": "Number"
        }
        max = len(json_text['words'])-1

        notdone = True
        time = datetime.datetime.now().timestamp()

        while(notdone):
            idx = random.randrange(0,max)
            #only replace certain tags
            if(json_text['pos'][idx] in VALID_TAGS and json_text['words'][idx] != "%%%"):
                json_text['words'][idx] = "%%%"
                json_text['pos'][idx] = UPOS_TO_ENGLISH[json_text['pos'][idx]] #make spacy upos readable by users
                notdone = False
            if datetime.datetime.now().timestamp()-time > MAXLOOPTIME:
                notdone = False
        return json_text


