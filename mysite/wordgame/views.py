import operator
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from .services import NLPServices, PrefVector, CurrentHeadlineServices, BlurbServices, LanguageServices
from .view_helpers import create_context_for_main_template, get_or_create_prefvector, get_client_ip


@csrf_exempt
def audio(request):
    try:
        print("audio recording post")
        files= request.FILES
        blob = files['audioRecording']
        print("sound blob len", len(blob))
        file = blob.read()

        s = LanguageServices()
        searchterm = s.speech_to_text(file)
        searchterm = searchterm.replace(".","")
        searchterm = searchterm.replace(",","")
        searchterm = searchterm.replace(" ", "%20")
        print("search term will be:",searchterm)

        c = CurrentHeadlineServices()
        text = c.get_search_headline(searchterm)
        print("blurb will be:",text)
        request.session['custom'] = "True"
        request.session['text'] = text
        print("success, redirecting...")
        return HttpResponse("success")
    except Exception as e:
        print("failure",e)
        return HttpResponseBadRequest("failure")

@csrf_exempt
def tts(request):
    sessionid = request.session.session_key
    print("sessionid filename will be: ", sessionid)
    text = request.POST['text']
    print("text is: ", text)
    l = LanguageServices()
    bytes = l.text_to_speech(text, sessionid)
    if bytes is not None:
        response = HttpResponse(bytes, content_type='audio/mp3')
        response['Content-Disposition'] = 'attachment; filename="audiofilename"'
        return response
    return HttpResponseBadRequest("failure")

def custom(request):
    print("custom request")
    text = request.session.get('text')

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)


def index(request):
    prefvector = request.session.get('prefvector')
    if prefvector is None:
        return HttpResponseRedirect('/wordgame/new')

    prefvector = json.loads(prefvector)
    prefvector = PrefVector.get_as_vector(prefvector)

    #get blurb based on user prefs
    b = BlurbServices()
    blurb = b.get_blurb(prefvector)
    sv = json.loads(str(blurb.scorevector))

    context = create_context_for_main_template(blurb.text,sv)
    return render(request, 'wordgame/index.html', context)


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

    if text != "-1":
        print("got local headline, rendering...")
        context = create_context_for_main_template(text)
        return render(request, 'wordgame/index.html', context)
    else:
        print("could not get local headline, sending to default...")
        return HttpResponseRedirect('/wordgame/')

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

    vote = request.POST['vote']
    print("user voted:",vote)
    if vote != "-1":
        # update pref vector
        prefvector = PrefVector.record_vote(prefvector, maxcategory, vote)
        print("new pref vector is: ", prefvector)
    else:
        print("no valid vote, got:",vote)

    #store new vect in session
    request.session['prefvector'] = json.dumps(prefvector)

    if "current" in request.POST:
        print("sending to current headline")
        return HttpResponseRedirect('/wordgame/current/')
    elif "local" in request.POST:
        print("sending to local headline")
        return HttpResponseRedirect('/wordgame/local/')
    else:
        return HttpResponseRedirect('/wordgame/')
