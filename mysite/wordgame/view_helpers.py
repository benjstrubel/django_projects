import json
from .services import NLPServices


def create_context_for_main_template(text, json_scorevector=None):
    n = NLPServices()
    # tag pos in text
    jsontext = n.tag_blurb(text)
    #remove some pos for mad lib
    jsontext = n.prep_blurb(jsontext)

    if json_scorevector is None:
        json_scorevector = n.classify_headline(text)

    context = {
        'blurbzip' : zip(jsontext['words'],jsontext['pos']),
        'blurb' : jsontext['words'],
        'scorevector' : json_scorevector
    }
    return context

def get_or_create_prefvector(request):
    prefvector = request.session.get('prefvector')
    print("prefvector is: ", prefvector)
    if prefvector is None or len(prefvector) == 0:
        print("bad or missing pref vector, resetting...")
        prefvector ={"entertainment" : .5, "health" : .5, "politics" : .5, "sports" : .5, "tech" : .5}
    else:
        prefvector = json.loads(prefvector)
    return prefvector

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        #get first in list which should be 'real' ip
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip