from django.shortcuts import render
import feedparser
import random
import json
from .serializers import BlurbSerializer
from rest_framework import generics
from .services import NLPServices
from .services import BlurbServices
from .models import Blurb

class BlurbListCreate(generics.ListCreateAPIView):
    queryset = Blurb.objects.all()
    serializer_class = BlurbSerializer

def index(request):

    #B = BlurbServices()
    #blurb = B.get_blurb("mock")
    blurb = Blurb.object.latest('id')
    context = {
        blurb
    }
    return render(request, 'wordgame/index.html', context)

def notindex(request):
    n = NLPServices()

    feed = feedparser.parse("https://www.cbssports.com/rss/headlines/")
    idx = random.randrange(0,len(feed)-1)
    blurb_text = feed.entries[idx].title

    blurb_dict = json.loads(n.get_pos_tags(blurb_text))

    str_pos = ""
    for pos in blurb_dict['pos']:
        str_pos += pos + " "
    str_words = ""
    for word in blurb_dict['words']:
        str_words += word + " "


    context = {
        'blurb': str_words,
        'pos' : str_pos,
    }
    return render(request, 'wordgame/index.html', context)
