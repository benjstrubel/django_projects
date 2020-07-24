import json

from django.db import models

# Create your models here.
class Blurb(models.Model):
    text = models.TextField()

class ScoreVector(models.Model):
    blurb = models.OneToOneField(Blurb, on_delete=models.CASCADE)
    entertainment_score = models.FloatField()
    health_score = models.FloatField()
    politics_score = models.FloatField()
    sports_score = models.FloatField()
    tech_score = models.FloatField()

    def __str__(self):
        sv_dict = {
            "entertainment": self.entertainment_score,
            "health": self.health_score,
            "politics": self.politics_score,
            "sports": self.sports_score,
            "tech": self.tech_score
        }
        return json.dumps(sv_dict)

