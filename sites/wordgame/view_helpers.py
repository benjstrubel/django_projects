import json
import logging
import operator
from django.contrib.auth.models import User
from .services import NLPServices
from .models import SessionPreferenceVector, PreferenceVector

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


def get_max_category(request):
    """Get's the max category of the blurb that the user just voted on

    Args:
        param1 (request): http request

    Returns:
        String: name of category that is the category with highest score
    """
    #get category vector of blurb they voted on
    sv = request.POST["sv"]
    print(sv)
    sv = sv.replace("'",'"')
    sv = json.loads(sv)
    #get max category
    maxcategory = max(sv.items(), key=operator.itemgetter(1))[0]
    logger.info("max category is " + maxcategory)
    return maxcategory


def save_user_prefs(request, sessionprefvec_obj):
    """Saves user preferences

    Called after user's vote on topic is recorded
    Updates all user prferencs and saves in db

    Args:
        param1 (request): http request
        param2 (SessionPReferenceVector): Users current preferences

    Returns:
        None
    """
    user = User.objects.get(id=request.user.id)
    for cat, score in sessionprefvec_obj.prefs.items():
        prefvec = PreferenceVector(user=user, category=cat, score=score)
        prefvec.save()

#helper function to render context for the main page
def create_context_for_main_template(text, json_scorevector=None):
    """Helper function to prep a blurb for display

    Preps blurb and then adds appropriate fields to context before returning

    Args:
        param1 (string): text of blurb
        param2 (string): score vector for blurb

    Returns:
        Context object
    """
    nlp = NLPServices()
    # tag pos in text
    jsontext = nlp.tag_blurb(text)

    #remove some pos for mad lib
    jsontext = nlp.prep_blurb(jsontext)

    #classify headline if not from db
    if json_scorevector is None:
        json_scorevector = nlp.classify_headline(text)

    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'scorevector' : json_scorevector
    }
    return context


def get_or_create_prefvector(request):
    """Gets user preferences for current session or creates new if unavailable
    handles edge cases of pref vector being invalid or not set for any reason

    Args:
        param1 (request): request

    Returns:
        String
    """
    if request.session.get('preferencevector') is not None:
        logger.debug("returning existing session vector")
        serialized_session_vector = request.session.get('preferencevector')
        #serialized_session_vector = '{"business": 0.5, "technology": 0.5, "sports": 0.5, "entertainment": 0.5, "politics": 0.5, "travel": 0.5, "health": 0.5}'
        logger.debug(serialized_session_vector)
        return json.loads(serialized_session_vector,cls=SessionPreferenceVector)

    if request.user.is_authenticated:
        logger.debug("user authenticated, fetching saved preferences")
        user = User.objects.get(id=request.user.id)
        pref_vec_list =  user.preferencevector_set.all()
        new_session_pref_vec = SessionPreferenceVector()
        new_session_pref_vec.set_categories_from_preference_vectors(pref_vec_list)
        # store vect in session
        request.session['preferencevector'] = json.dumps(new_session_pref_vec, default=SessionPreferenceVector.encode)
        return new_session_pref_vec

    logger.debug("creating new sessionprefvector")
    new_session_pref_vec = SessionPreferenceVector()
    new_session_pref_vec.initialize_as_default()
    return new_session_pref_vec



def get_client_ip(request):
    """Get client ip if they want local headline


    Args:
        param1 (request): request

    Returns:
        String ip address in dot notation
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        #get first in list which should be 'real' ip
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip