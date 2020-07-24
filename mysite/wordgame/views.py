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
    prefvector = request.session.get('prefvector')
    if prefvector is None:
        return HttpResponseRedirect('/wordgame/new')

    #convert session pref vector to json and get as actual vector
    prefvector = json.loads(prefvector)
    prefvector = PrefVector.get_as_vector(prefvector)

    #get blurb based on user prefs
    b = BlurbServices()
    blurb = b.get_blurb(prefvector)
    sv = blurb.scorevector
    jsontext = b.process_blurb(blurb)

    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'blurb_id' : blurb.id,
        'scorevector' : sv
    }
    return render(request, 'wordgame/index.html', context)

def get_or_create_prefvector(request):
    prefvector = request.session.get('prefvector')
    print("prefvector is: ", prefvector)
    if prefvector is None or len(prefvector) == 0:
        print("bad pref vector reseting...")
        prefvector ={"entertainment" : .5, "health" : .5, "politics" : .5, "sports" : .5, "tech" : .5}
    else:
        prefvector = json.loads(prefvector)
    return prefvector

def newsession(request):
    context = {}
    return render(request, 'wordgame/new.html', context)

def initialvote(request):
    category = request.POST['category']
    prefvector = get_or_create_prefvector(request)

    if category is not None:
        #record a positive vote for chosen category
        prefvector = PrefVector.record_vote(prefvector,category,"1")

    request.session['prefvector'] = json.dumps(prefvector)

    return HttpResponseRedirect('/wordgame/')

def vote(request):
    prefvector = get_or_create_prefvector(request)

    b = BlurbServices()
    blurb = get_object_or_404(Blurb, pk=request.POST['blurb_id'])
    # get highest category
    maxcategory = b.get_highest_cat(blurb)
    print("max category is: ", maxcategory)

    #get their up/down vote
    if request.POST.get('upvote'):
        vote = "1"
    elif request.POST.get('downvote'):
        vote = "0"
    else:
        print("bad vote, using 1")
        vote = "1"

    print("user voted it: ", vote)

    #update pref vector
    prefvector = PrefVector.record_vote(prefvector, maxcategory, vote)
    print("new pref vector is: ", prefvector)

    #store new vect in session
    request.session['prefvector'] = json.dumps(prefvector)

    return HttpResponseRedirect('/wordgame/')
