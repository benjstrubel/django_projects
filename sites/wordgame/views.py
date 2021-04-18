import operator
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.urls import reverse
from .forms import CustomUserCreationForm
from django.views.decorators.csrf import csrf_exempt
import json
from .services import  PrefVector, CurrentHeadlineServices, BlurbServices, LanguageServices
from .models import Creation
from .view_helpers import create_context_for_main_template, get_or_create_prefvector, get_client_ip


#process speech to text request
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
        #remove invalid characters for Google RSS search
        searchterm = searchterm.replace(".","")
        searchterm = searchterm.replace(",","")
        searchterm = searchterm.replace(" ", "%20") #space to %20
        print("search term will be:",searchterm)

        #create current head line service object to get headline based on voice to text search term
        c = CurrentHeadlineServices()
        text = c.get_search_headline(searchterm)
        print("blurb will be:",text)
        request.session['custom'] = "True" #set session custom variable to true so we know to render custom text
        request.session['text'] = text #store text in session variabe
        print("success, redirecting...")
        return HttpResponse("success")
    except Exception as e:
        print("failure",e)
        return HttpResponseBadRequest("failure")

#text to speech
@csrf_exempt
def tts(request):
    #use session id so we have unique filename
    sessionid = request.session.session_key
    print("sessionid filename will be: ", sessionid)
    text = request.POST['text']
    print("text is: ", text)

    #create language services object to do text to speech
    l = LanguageServices()
    bytes = l.text_to_speech(text, sessionid)
    #if we have a valid file return contents in response
    if bytes is not None:
        response = HttpResponse(bytes, content_type='audio/mp3')
        response['Content-Disposition'] = 'attachment; filename="audiofilename"'
        return response
    #if process failed, return failure
    return HttpResponseBadRequest("failure")

#function to process custom speech to text headline, text of blurb is stored in session variable
def custom(request):
    print("custom request")
    text = request.session.get('text')

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)

#main page view function
def index(request):
    #get user pref vector, if not set render new page so user can choose fav topic
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

#function for current headline
def current_headline(request):
    #get pref vector and then max category
    prefvector = get_or_create_prefvector(request)
    maxcategory = max(prefvector.items(), key=operator.itemgetter(1))[0]

    #get headline for that cat
    c = CurrentHeadlineServices()
    text = c.get_current_headline(maxcategory)

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)

#function for local headline based on ip
def local_headline(request):
    #attempt to get location based on ip and get headline for that state and country
    ip = get_client_ip(request)
    c = CurrentHeadlineServices()
    text = c.get_local_headline(ip)

    #if successful render local headline
    if text != "-1":
        print("got local headline, rendering...")
        context = create_context_for_main_template(text)
        return render(request, 'wordgame/index.html', context)
    #if error, just get from db
    else:
        print("could not get local headline, sending to default...")
        return HttpResponseRedirect('/wordgame/')

#function for new user/session
def newsession(request):
    context = {}
    return render(request, 'wordgame/new.html', context)

#handle post request for intial vote from new user/session
def initialvote(request):
    category = request.POST['category']
    prefvector = get_or_create_prefvector(request)

    if category is not None:
        #record a positive vote for chosen category
        prefvector = PrefVector.record_vote(prefvector,category,"1")

    request.session['prefvector'] = json.dumps(prefvector)
    return HttpResponseRedirect('/wordgame/')

#handle post request when user is done and request enw game (local, current, custom, or stored)
def vote(request):
    #get user pref vector
    prefvector = get_or_create_prefvector(request)
    #get category vector of blurb they voted on
    sv = request.POST["sv"]
    sv = sv.replace("'",'"')
    sv = json.loads(sv)

    #get max category
    maxcategory = max(sv.items(), key=operator.itemgetter(1))[0]
    print("max category is: " , maxcategory)

    #if they voted, record vote and update pref vector
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

    #redirect based on what option button they clicked
    if "current" in request.POST:
        print("sending to current headline")
        return HttpResponseRedirect('/wordgame/current/')
    elif "local" in request.POST:
        print("sending to local headline")
        return HttpResponseRedirect('/wordgame/local/')
    else:
        return HttpResponseRedirect('/wordgame/')

def creations(request):
    context = {}
    creations = Creation.objects.filter(public=True).order_by('-rank')
    print('found ' + str(len(creations)) + ' public creations')
    context['creations'] = creations
    return render(request, 'wordgame/creations.html', context)

def creationvote(request):
    if request.user.is_authenticated:
        print('user authenticated, processing vote')
        try:
            vote = [key for key, val in request.POST.items() if 'vote' in key]
            splits = vote[0].split('-')
            id = splits[2]
            updown = splits[1]
            if 'up' in updown:
                value = 1
            elif 'down' in updown:
                value = -1
            else:
                value = 0
                print('could not parse vote value')
            vote_on_creation(id, value)
        except:
            print('error processing vote')

    else:
        print('user not authenticated, ignoring vote')

    return redirect(reverse("creations"))

def vote_on_creation(id, vote):
    creation = Creation.objects.get(pk=id)
    creation.rank = creation.rank + vote if creation.rank is not None else vote
    creation.save()

def creationdelete(request):
    if request.user.is_authenticated:
        print(request.POST)
        id = request.POST['cid']
        creation = Creation.objects.get(id=id)
        if creation.public is False:
            creation.delete()

    return redirect(reverse("dashboard"))

def dashboard(request):
    context = {}
    user = request.user
    print('user id:' + str(user.id))
    creations = Creation.objects.filter(user=user.id)
    print(len(creations))
    context['creations'] = creations
    return render(request, 'wordgame/dashboard.html', context)

def register(request):
    if request.method == "GET":
        return render(
            request, "wordgame/register.html",
            {"form": CustomUserCreationForm}
        )
    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("dashboard"))


