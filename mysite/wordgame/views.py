import operator
import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import random
import json
from .services import NLPServices, PrefVector, CurrentHeadlineServices
from .services import BlurbServices
from .models import Blurb
from .models import ScoreVector
from google.cloud import speech_v1
from google.cloud.speech import types
from google.cloud.speech import enums
from google.oauth2 import service_account

@csrf_exempt
def audio(request):
    #print(request.body)
    #blob = request.body
    #blob = request.POST['audioRecording']
    #print(blob)
    blob = request.FILES['audioRecording']
    print("sound blob len", len(blob))
    file = os.getcwd() + os.sep + "\wordgame\speechrecognition-bb13d77a6e29.json"
    credentials = service_account.Credentials.from_service_account_file(file)
    client = speech_v1.SpeechClient(credentials=credentials)
    audio = types.RecognitionAudio(content=blob.read())
    config = types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.OGG_OPUS, language_code='en-US')
    resp = client.recognize(config, audio)
    for alternative in resp:
        print('Transcript: {}'.format(alternative.transcript))
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
    sv = blurb.scorevector

    jsontext = b.process_blurb(blurb)
    n = NLPServices()
    jsontext = n.prep_blurb(jsontext)

    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'blurb_id' : blurb.id,
        'scorevector' : json.loads(str(sv))
    }
    return render(request, 'wordgame/index.html', context)

def current_headline(request):
    prefvector = get_or_create_prefvector(request)
    maxcategory = max(prefvector.items(), key=operator.itemgetter(1))[0]

    #get headline for that cat
    c = CurrentHeadlineServices()
    text = c.get_current_headline(maxcategory)

    #classify headline
    n = NLPServices()
    score_vector =n.classify_headline(text)
    print("score vector from nlp server is:", score_vector)

    #pos tag headline text
    jsontext = n.tag_blurb(text)
    jsontext = n.prep_blurb(jsontext)
    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'blurb_id' : -1,
        'scorevector' : score_vector
    }
    return render(request, 'wordgame/index.html', context)


def get_or_create_prefvector(request):
    prefvector = request.session.get('prefvector')
    print("prefvector is: ", prefvector)
    if prefvector is None or len(prefvector) == 0:
        print("bad or missing pref vector, resetting...")
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
    sv = request.POST["sv"]
    sv = sv.replace("'",'"')
    sv = json.loads(sv)

    if request.POST['blurb_id'] != "-1":
        b = BlurbServices()
        blurb = get_object_or_404(Blurb, pk=request.POST['blurb_id'])
        # get highest category
        maxcategory = b.get_highest_cat(blurb)
        print("max category is: ", maxcategory)
    else:
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
