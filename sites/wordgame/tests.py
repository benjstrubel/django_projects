from django.test import TestCase
from .models import Blurb, User, Creation, PreferenceVector, ScoreVectorNew
from .services import CurrentHeadlineServices, BlurbServices, LanguageServices, NLPServices

class ModelsTestCase(TestCase):
    def setUp(self):
        Blurb.objects.create(id=0, text="This is a test blurb")
        User.objects.create(username='TestUser',password='password')

    def test_blurb(self):
        blurb = Blurb.objects.get(id=0)
        self.assertIsNotNone(blurb)

    def test_creation(self):
        user = User.objects.get(username='TestUser')
        Creation.objects.create(id=0,user=user,text='Test user creation',public=True)
        creation = Creation.objects.get(id=0)
        self.assertIsNotNone(creation)

    def test_preference_vector(self):
        cats = ["sports","entertainment","technology","politics","health","travel","business"]
        user = User.objects.get(username='TestUser')
        for cat in cats:
            PreferenceVector.objects.create(user=user,category=cat,score=0)
        userprefs = PreferenceVector.objects.filter(user=user)
        self.assertEquals(len(userprefs),7)

class CurrentHeadlineServicesTestCase(TestCase):
    def setUp(self):
        self.cur_svc = CurrentHeadlineServices()

    def test_local_headline(self):
        ip='131.196.54.38' #baltimore
        headline = self.cur_svc.get_local_headline(ip)
        self.assertIsNot(headline, "-1")

    def test_search_headline(self):
        search_phrase = "Philadelphia%20Eagles"
        headline = self.cur_svc.get_search_headline(search_phrase)
        self.assertIsNotNone(headline)

    def test_current_headline(self):
        cats = ["sports","entertainment","technology","politics","health","travel","business"]
        for cat in cats:
            headline = self.cur_svc.get_current_headline(cat)
            self.assertIsNotNone(headline)

class BlurbServicesTestCase(TestCase):
    def setUp(self):
        self.blurb_svc = BlurbServices()

    def test_blurb_score(self):
        blurb = Blurb(id=0,text="Test blurb")
        blurb.save()
        cats_and_scores = {"sports":.99, "entertainment" : 0.0, "technology" : 0.0, "politics" : 0.0, "health" : 0.0, "business" : 0.0, "travel" : 0.0}
        for cat,score in cats_and_scores.items():
            svn = ScoreVectorNew(blurb=blurb,category=cat,score=score)
            svn.save()

        bsvs = BlurbServices()
        highest_score_cat = bsvs.get_highest_cat(blurb)
        self.assertEquals(highest_score_cat, 'sports')

class LanguageServicesTestCase(TestCase):
    def setUp(self):
        self.lang_svc = LanguageServices()

    def test_text_to_speech(self):
        #uncomment to test on server, will not work on windows
        #test_text = "This is a speech to text test."
        #audio_bytes = self.lang_svc.text_to_speech(test_text, "dummyid")
        #self.assertIsNotNone(audio_bytes)
        self.assertIsNone(None)

class NLPServicesTestCase(TestCase):
    def setUp(self):
        self.nlp_svc = NLPServices()

    def test_pos_tag(self):
        sentence = "The quick dog jumped over the fence."
        expected_result = {'words': ['The', 'quick', 'dog', 'jumped', 'over', 'the', 'fence', '.'], 'pos': ['DT', 'JJ', 'NN', 'VBD', 'IN', 'DT', 'NN', '.']}
        result = self.nlp_svc.tag_blurb(sentence)
        self.assertEquals(result,expected_result,"NLP server returned unexpected result")

    def test_classify(self):
        sentence = "THe NFL and the NBA are football and basketball leagues filled with sports teams that play games. People loves sports and competitions with winners."
        result = self.nlp_svc.classify_headline(sentence)
        self.assertIsNotNone(result,"No result returned by NLP Server")

    def test_prep_blurb(self):
        test_json_text = {'words': ['The', 'quick', 'dog', 'jumped', 'over', 'the', 'fence', '.'],
                           'pos': ['DT', 'JJ', 'NN', 'VBD', 'IN', 'DT', 'NN', '.']}
        prepped_result = self.nlp_svc.prep_blurb(test_json_text)
        count = 0
        expected_count = 3
        for word in prepped_result['words']:
            if '%' in word: count+=1
        self.assertEquals(count,expected_count,"Expected number of words not removed.")



