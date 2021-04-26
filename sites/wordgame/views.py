import operator
import logging
import json

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.urls import reverse
from .forms import CustomUserCreationForm
from django.views.decorators.csrf import csrf_exempt
from .services import CurrentHeadlineServices, BlurbServices, LanguageServices, PreferenceServices
from .models import Creation, SessionPreferenceVector
from .view_helpers import create_context_for_main_template, get_or_create_prefvector, get_client_ip, save_user_prefs
from .view_helpers import get_max_category

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    }
})
logger = logging.getLogger(__name__)


@csrf_exempt
def audio(request):
    """Speech to text request
    Uses cloud service implemented in Services module

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    try:
        logger.debug("audio recording post")
        files= request.FILES
        blob = files['audioRecording']
        logger.debug("sound blob len", len(blob))
        file = blob.read()

        s = LanguageServices()
        searchterm = s.speech_to_text(file)
        #remove invalid characters for Google RSS search
        searchterm = searchterm.replace(".","")
        searchterm = searchterm.replace(",","")
        searchterm = searchterm.replace(" ", "%20") #space to %20
        logger.info("audio to text search term will be:",searchterm)

        #create current head line service object to get headline based on voice to text search term
        c = CurrentHeadlineServices()
        text = c.get_search_headline(searchterm)
        logger.debug("blurb will be:",text)
        request.session['custom'] = "True" #set session custom variable to true so we know to render custom text
        request.session['text'] = text #store text in session variabe
        logger.debug("success, redirecting...")
        return HttpResponse("success")
    except Exception as e:
        logger.error("failure",e)
        return HttpResponseBadRequest("failure")


@csrf_exempt
def tts(request):
    """Text-To-Speech request
    Uses local tts engine implemented in Services module

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    #use session id so we have unique filename
    sessionid = request.session.session_key
    logger.info("sessionid filename will be: ", sessionid)
    text = request.POST['text']
    logger.debug("text is: ", text)

    #create language services object to do text to speech
    l = LanguageServices()
    bytes = l.text_to_speech(text, sessionid)
    #if we have a valid file return contents in response
    if bytes is not None:
        response = HttpResponse(bytes, content_type='audio/mp3')
        response['Content-Disposition'] = 'attachment; filename="audiofilename"'
        logger.info("audio filed created successfully")
        return response
    #if process failed, return failure
    logger.error("could not create audio file")
    return HttpResponseBadRequest("failure")


def custom(request):
    """Process custom speech to text headline
    text of blurb is stored in session variable

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    text = request.session.get('text')
    logger.info("custom request " + text)
    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)


def index(request):
    """Main game view page

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    #get user pref vector, if not set render new page so user can choose fav topic
    #prefvector = request.session.get('prefvector')
    prefvector_str = request.session.get('preferencevector')
    if prefvector_str is None:
        return HttpResponseRedirect('/wordgame/new')

    prefvector_obj = json.loads(prefvector_str,cls=SessionPreferenceVector)
    print(prefvector_obj.__class__)

    #get blurb based on user prefs
    blurb_svcs = BlurbServices()
    blurb = blurb_svcs.get_blurb(prefvector_obj)
    ##sv = json.loads(str(blurb.scorevector))
    sv = blurb_svcs.get_blurbs_scores_as_dict(blurb.id)

    context = create_context_for_main_template(blurb.text,sv)
    return render(request, 'wordgame/index.html', context)


def current_headline(request):
    """Current headline view

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    #get pref vector and then max category
    sessionprefvec_obj = get_or_create_prefvector(request)
    maxcategory = sessionprefvec_obj.get_max_cat()
    logger.info("getting current headline for " + maxcategory)

    #get headline for that cat
    c = CurrentHeadlineServices()
    text = c.get_current_headline(maxcategory)

    context = create_context_for_main_template(text)
    return render(request, 'wordgame/index.html', context)


def local_headline(request):
    """Local headline based on IP geo location

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    #attempt to get location based on ip and get headline for that state and country
    ip = get_client_ip(request)
    c = CurrentHeadlineServices()
    text = c.get_local_headline(ip)

    #if successful render local headline
    if text != "-1":
        logger.info("got local headline, rendering...")
        context = create_context_for_main_template(text)
        return render(request, 'wordgame/index.html', context)
    #if error, just get from db
    else:
        logger.warning("could not get local headline, sending to default...")
        return HttpResponseRedirect('/wordgame/')


def newsession(request):
    """Display new user category selection page

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    context = {}
    return render(request, 'wordgame/new.html', context)


def initialvote(request):
    """Handle POST request for user initial vote cold start

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    category = request.POST['category']
    logger.info("new user picked " + category)
    sessionprefvector_obj = get_or_create_prefvector(request)

    if category is not None:
        #record a positive vote for chosen category
        pref_svs = PreferenceServices()
        sessionprefvector_obj = pref_svs.record_vote(sessionprefvector_obj, category,"1")

    request.session['preferencevector'] = json.dumps(sessionprefvector_obj,default=SessionPreferenceVector.encode)
    return HttpResponseRedirect('/wordgame/')


def vote(request):
    """Handle POST request when user is done with game and has submitted feedback

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    #get user pref vector
    sessionprefvec_obj = get_or_create_prefvector(request)

    maxcategory = get_max_category(request)
    logger.debug("max category is: " , maxcategory)

    #if they voted, record vote and update pref vector
    vote = request.POST['vote']
    logger.debug("user voted:",vote)
    if vote != "-1":
        # update pref vector
        pref_svcs = PreferenceServices()
        sessionprefvec_obj = pref_svcs.record_vote(sessionprefvec_obj, maxcategory, vote)
        logger.info("new pref vector is: " + str(sessionprefvec_obj))
    else:
        logger.debug("no valid vote, got: " + str(vote))

    #store new vect in session
    request.session['preferencevector'] = json.dumps(sessionprefvec_obj,default=SessionPreferenceVector.encode)

    #update user prefs if logged in
    if request.user.is_authenticated:
        logger.debug("saving user preferences...")
        save_user_prefs(request, sessionprefvec_obj)


    #redirect based on what option button they clicked
    if "current" in request.POST:
        logger.debug("sending to current headline")
        return HttpResponseRedirect('/wordgame/current/')
    elif "local" in request.POST:
        logger.debug("sending to local headline")
        return HttpResponseRedirect('/wordgame/local/')
    else:
        return HttpResponseRedirect('/wordgame/')

def creations(request):
    """Display all public creations

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    context = {}
    creations = Creation.objects.filter(public=True).order_by('-rank')
    logger.debug('found ' + str(len(creations)) + ' public creations')
    context['creations'] = creations
    return render(request, 'wordgame/creations.html', context)

def creationvote(request):
    """Handle POST request of vote on public creations

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    if request.user.is_authenticated:
        logger.debug('user authenticated, processing vote')
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
                logger.error('could not parse vote value')
            vote_on_creation(id, value)
        except:
            logger.error('error processing vote')

    else:
        logger.warning('user not authenticated, ignoring vote')

    return redirect(reverse("creations"))

def vote_on_creation(id, vote):
    """Record user vote of public creation

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    creation = Creation.objects.get(pk=id)
    creation.rank = creation.rank + vote if creation.rank is not None else vote
    creation.save()

def creationdelete(request):
    """Delete saved creation

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    if request.user.is_authenticated:
        logger.debug(request.POST)
        id = request.POST['cid']
        creation = Creation.objects.get(id=id)
        if creation.public is False:
            creation.delete()

    return redirect(reverse("dashboard"))

def dashboard(request):
    """Logged in user main dashboard

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
    context = {}
    user = request.user
    logger.info('user id:' + str(user.id))
    creations = Creation.objects.filter(user=user.id)
    logger.debug("user creations size " + str(len(creations)))
    context['creations'] = creations
    return render(request, 'wordgame/dashboard.html', context)

def register(request):
    """Handlenew user gistration

    Args:
        param1 (request): http request

    Returns:
        Render method
    """
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
