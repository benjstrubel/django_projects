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

