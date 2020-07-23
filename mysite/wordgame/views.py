from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
import feedparser
import random
import json
from .services import NLPServices, PrefVector
from .services import BlurbServices
from .models import Blurb
from .models import ScoreVector


def index(request):

    b = BlurbServices()
    blurb = b.get_blurb("dummy vector")
    sv = blurb.scorevector
    jsontext = b.process_blurb(blurb)

    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'blurb_id' : blurb.id,
        'scorevector' : sv
    }
    return render(request, 'wordgame/index.html', context)

def vote(request):
    print(request.session.items())
    #get users pref vector from session store
    #request.session.flush()
    prefvector = request.session.get('prefvector')

    if prefvector is None or len(prefvector) == 0:
        print("bad pref vector reseting...")
        prefvector ={"entertainment" : .5, "health" : .5, "politics" : .5, "sports" : .5, "tech" : .5}
    else:
        prefvector = json.loads(prefvector)

    print("old prefvector is: ", prefvector)
    b = BlurbServices()
    blurb = get_object_or_404(Blurb, pk=request.POST['blurb_id'])
    # get highest category
    maxcategory = b.get_highest_cat(blurb)
    print("max category is: ", maxcategory)

    #get their up/down vote
    vote = request.POST['vote'].strip()
    print("user voted it: ", vote)

    #update pref vector
    prefvector = PrefVector.record_vote(prefvector, maxcategory, vote)
    print("new pref vector is: ", prefvector)

    #store new vect in session
    request.session['prefvector'] = json.dumps(prefvector)

    return HttpResponseRedirect('/wordgame/')


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
