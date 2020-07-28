import operator
import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import random
import json
from .services import NLPServices, PrefVector, CurrentHeadlineServices, BlurbServices, LanguageServices
from .models import Blurb
from .models import ScoreVector
from .view_helpers import create_context_for_main_template, get_or_create_prefvector, get_client_ip


@csrf_exempt
def audio(request):
    #print(request.body)
    #blob = request.body
    #blob = request.POST['audioRecording']
    #print(blob)
    blob = request.FILES['audioRecording']
    print("sound blob len", len(blob))
    file = blob.read()

    s = LanguageServices()
    searchterm = s.speech_to_text(file)

    context = {
        'audioRecording' : blob
    }
    return render(request, 'wordgame/audiotest.html', context)


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
    sv = json.loads(str(blurb.scorevector))

    context = create_context_for_main_template(blurb.text,sv)
    return render(request, 'wordgame/index.html', context)

def submit(request):

    #process vote

    #
    pass



def current_headline(request):
    prefvector = get_or_create_prefvector(request)
    maxcategory = max(prefvector.items(), key=operator.itemgetter(1))[0]

    #get headline for that cat
    c = CurrentHeadlineServices()
    text = c.get_current_headline(maxcategory)

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)


def local_headline(request):
    ip = get_client_ip(request)
    c = CurrentHeadlineServices()
    text = c.get_local_headline(ip)

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)

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
    sv = request.POST["sv"]
    sv = sv.replace("'",'"')
    sv = json.loads(sv)

    maxcategory = max(sv.items(), key=operator.itemgetter(1))[0]
    print("max category is: " , maxcategory)

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
