import json
from django.db import models
from django.contrib.auth.models import User



class Creation(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    text = models.TextField()
    public = models.BooleanField(null=True, blank=False, default=False)
    rank = models.IntegerField(null=True, blank=True)

class PreferenceVector(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    category = models.TextField()
    score = models.FloatField()

    def getDefaultModel(self):
        pass

class Blurb(models.Model):
    text = models.TextField()

class ScoreVectorNew(models.Model):
    blurb = models.OneToOneField(Blurb, on_delete=models.CASCADE)
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

