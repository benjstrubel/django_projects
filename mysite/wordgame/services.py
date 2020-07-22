import random
from scipy.spatial.distance import cosine
import socket
import struct
import re
import datetime
from .models import Blurb
from django.contrib.sessions.backends.db import SessionStore

class PrefVector:
    INCREMENT = .1
    dict = {}

    def __init__(self):
        self.dict['entertainment'] = 0.01
        self.dict['health'] = 0.01
        self.dict['politics'] = 0.01
        self.dict['sports'] =0.01
        self.dict['tech'] = 0.01

    def like(self,category):
        self.dict[category] += self.INCREMENT

    def get_as_vector(self):
        #hardcoding to make sure order is correct
        v = list()
        v.append(self.dict['entertainment'])
        v.append(self.dict['health'])
        v.append(self.dict['politics'])
        v.append(self.dict['sports'])
        v.append(self.dict['tech'])
        return v



class BlurbServices:

    def get_blurb(self, pref_vector):
        #get pref vector from session
        pref_vector = [0,0,1,0,0]

        #store pk_id:cosine_sim_score
        sim_scores = {}

        #calc all cosine sim scores
        #TODO: rewrite to use heap to avoid sorting entire set at end
        for blurb in Blurb.objects.all():
            blurb_vector = [blurb.entertainment_score,blurb.health_score,blurb.politics_score,blurb.sports_score,blurb.tech_score]
            cosine_sim_score = 1 - cosine(pref_vector,blurb_vector)
            sim_scores[blurb.pk] = cosine_sim_score

        #order by cosine sim scores and get random high score
        sorted_sim_scores = sorted(sim_scores.items(),key=lambda x: x[1],reverse=True)
        #
        #max = 100 if len(sorted_sim_scores) > 100 else len(sorted_sim_scores)
        #idx = random.randrange(0,max)
        pk = next(iter(sorted_sim_scores))[0]

        blurb = Blurb.objects.get(pk=pk)
        return blurb.text


class Preferences:
    def update_prefs(self):
        SessionStore
        pass

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

    def get_pos_tags(self, text):
        #connect to our nlp service

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('127.0.0.1', 9999)

        sock.connect(server_address)
        mymsg = Message.create_msg(text.encode())
        sock.sendall(mymsg)
        #until it can be fixed this infuriating line is needed in order to raise the underlying buffer available to be read flag on the server
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

        for x in range(0,WORD_REPLACE_COUNT-1):
            json_text = self.replace_pos(json_text)
        return json_text

    def replace_pos(self,json_text,x):
        MAXLOOPTIME = 2
        VALID_TAGS = ['NOUN', 'VERB', 'PROPN', 'ADV', 'ADJ', 'NUM']
        max = len(json_text)-1

        notdone = True
        time = datetime.datetime.now().timestamp()
        replaced_word = re.compile('%?%')
        while(notdone):
            idx = random.randrange(0,max)
            if(json_text[idx]['POS'] in VALID_TAGS and not re.match(replaced_word,json_text[idx]['word'])):
                json_text[idx]['word'] = "%{0}%".format(x)
                notdone = False
            if datetime.datetime.now().timestamp()-time > MAXLOOPTIME:
                notdone = False
        return json_text


