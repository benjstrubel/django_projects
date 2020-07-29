import random
import feedparser
import requests
from scipy.spatial.distance import cosine
import socket
import struct
import json
import datetime
from .models import Blurb

class PrefVector:
    INCREMENT = .2

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

    @staticmethod
    def like(pv, category):
        pv[category] += PrefVector.INCREMENT
        if pv[category] > 1:
            pv[category] = 1
        return pv

    @staticmethod
    def dislike(pv, category):
        pv[category] -= PrefVector.INCREMENT
        if pv[category] < 0:
            pv[category] = 0
        return pv

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

class LanguageServices:

    def speech_to_text(self, bytes):
        print("trying speech to text")
        url = "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US"
        headers = {
            'Ocp-Apim-Subscription-Key': 'ad6b74669fa84e05a99f4bb2861ddaae',
            'Content-type': 'audio/wav'
        }
        resp = requests.post(url, headers=headers, data=bytes)
        print("got resp from azure:",resp)
        guess = json.loads(resp.content.decode())
        print("guess is:",guess["DisplayText"])
        return guess["DisplayText"]


class CurrentHeadlineServices:

    def get_local_headline(self, ip):
        try:
            url = "http://ip-api.com/json/" + ip
            resp = requests.get(url)
            jsontext = json.loads(resp.content.decode())
            searchterm = jsontext['regionName'] + "," + jsontext['country']
            text = self.get_search_headline(searchterm)
        except Exception as e:
            print("error getting local headline")
            print(e)
            text = "-1"
        return text


    def get_search_headline(self, searchterm):
        url = "https://news.google.com/rss?q={0}&hl=en".format(searchterm)
        feed = feedparser.parse(url)
        entry = feed.entries[random.randrange(0, len(feed.entries))]
        text = entry.title
        return text

    def get_current_headline(self, category):
        urls = {
            "entertainment" : "http://rss.cnn.com/rss/cnn_showbiz.rss",
            "health" : "http://rss.cnn.com/rss/cnn_health.rss",
            "politics" : "http://rss.cnn.com/rss/cnn_allpolitics.rss",
            "sports" : "https://www.cbssports.com/rss/headlines/",
            "technology" : "http://rss.cnn.com/rss/cnn_tech.rss"
        }
        feed = feedparser.parse(urls[category])
        entry = feed.entries[random.randrange(0,len(feed.entries))]
        text = entry.title + ". " + entry.summary.split("<div")[0] + "."
        return text

class BlurbServices:
    def get_highest_cat(self, blurb):
        sv = blurb.scorevector

        #horrible code :(
        vect = [sv.entertainment_score,sv.health_score,sv.politics_score,sv.sports_score,sv.tech_score]
        print("finding max cat for this blurb vector:", vect)
        cats = ["entertainment","health","politics","sports","tech"]
        maxcat = cats[vect.index(max(vect))]
        print("max cat is:",maxcat)
        return maxcat

    def get_blurb(self, prefvector):
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
        #max = 100 if len(sorted_sim_scores) > 100 else len(sorted_sim_scores)
        #idx = random.randrange(0,max)
        pk = next(iter(sorted_sim_scores))[0]

        blurb = Blurb.objects.get(pk=pk)
        return blurb

    def process_blurb(self, blurb):
        #nlp text
        nlp = NLPServices()
        jsontext = nlp.tag_blurb(blurb.text)
        return jsontext

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

class NLPServices:
    def classify_headline(self, text):
        dict = {
            "cmd" : "classify",
            "payload" : text
        }
        msg = json.dumps(dict)
        text_score_vector = self.send_and_recv_msg(msg)
        return json.loads(text_score_vector)

    def tag_blurb(self, text):
        dict = {
            "cmd" : "postag",
            "payload" : text
        }
        msg = json.dumps(dict)
        tagged_blurb = self.send_and_recv_msg(msg)
        return json.loads(tagged_blurb)

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

    def prep_blurb(self, json_text):
        WORD_REPLACE_COUNT = 3
        for x in range(0,WORD_REPLACE_COUNT):
            json_text = self.replace_pos(json_text)
        return json_text

    def replace_pos(self,json_text):
        MAXLOOPTIME = 2
        VALID_TAGS = ['NOUN', 'VERB', 'PROPN', 'ADV', 'ADJ', 'NUM']
        max = len(json_text['words'])-1

        notdone = True
        time = datetime.datetime.now().timestamp()

        while(notdone):
            idx = random.randrange(0,max)
            if(json_text['pos'][idx] in VALID_TAGS and json_text['words'][idx] != "%%%"):
                json_text['words'][idx] = "%%%"
                notdone = False
            if datetime.datetime.now().timestamp()-time > MAXLOOPTIME:
                notdone = False
        return json_text


