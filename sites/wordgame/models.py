import json
from django.db import models
from django.contrib.auth.models import User
from .constants import Constants

class SessionPreferenceVector:
    def __init__(self):
        self.prefs = {}

    def get_max_cat(self):
        maxcat = ""
        maxval = -1
        for key,value in self.prefs.items():
            if value > maxval:
                maxcat = key
                maxval = value
        return maxcat

    def get_as_vec_order_by_cat(self):
        v = []
        for cat in Constants.CATEGORIES:
            v.append(self.prefs[cat])
        return v

    def initialize_as_default(self):
        for cat in Constants.CATEGORIES:
            self.prefs[cat] = 0.5

    def set_categories_from_preference_vectors(self, list):
        #initiliaze as default then replace with user settings
        self.initialize_as_default()
        for prefvec in list:
            self.prefs[prefvec.category] = prefvec.score


    def encode(self):
        return self.prefs

    def decode(self,dct):
        dct = json.loads(dct)
        spv = SessionPreferenceVector()
        spv.prefs = dct
        return spv

    def __str__(self):
        return json.dumps(self.prefs)

class Creation(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    text = models.TextField()
    public = models.BooleanField(null=True, blank=False, default=False)
    rank = models.IntegerField(null=True, blank=True)

class PreferenceVector(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    category = models.TextField()
    score = models.FloatField()

class Blurb(models.Model):
    text = models.TextField()

class ScoreVectorNew(models.Model):
    blurb = models.ForeignKey(Blurb, on_delete=models.CASCADE)
    category = models.TextField()
    score = models.FloatField()

class ScoreVector(models.Model):
    blurb = models.OneToOneField(Blurb, on_delete=models.CASCADE)
    entertainment_score = models.FloatField()
    health_score = models.FloatField()
    politics_score = models.FloatField()
    sports_score = models.FloatField()
    tech_score = models.FloatField()

    #override tostring, now to json format string
    def __str__(self):
        sv_dict = {
            "entertainment": self.entertainment_score,
            "health": self.health_score,
            "politics": self.politics_score,
            "sports": self.sports_score,
            "tech": self.tech_score
        }
        return json.dumps(sv_dict)

