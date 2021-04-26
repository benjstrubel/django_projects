from django.test import TestCase
from .models import Blurb, User, Creation, PreferenceVector, ScoreVectorNew
from .services import CurrentHeadlineServices, BlurbServices, LanguageServices

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
        cats = ["sports","entertainment","tech","politics","health","travel","business"]
        user = User.objects.get(username='TestUser')
        for cat in cats:
            PreferenceVector.objects.create(user=user,category=cat,score=0)
        userprefs = PreferenceVector.objects.filter(user=user)
        self.assertEquals(len(userprefs),5)

class CurrentHeadlineServicesTestCase(TestCase):
    def setUp(self):
        self.cur_svc = CurrentHeadlineServices()

    def test_local_headline(self):
        ip_list=['131.196.54.38','147.140. 127.133'] #baltimore, philadelphia
        for ip in ip_list:
            headline = self.cur_svc.get_local_headline(ip)
            self.assertIsNot(headline, "-1")

    def test_search_headline(self):
        search_phrase = "Philadelphia Eagles"
        headline = self.cur_svc.get_search_headline(search_phrase)
        self.assertIsNotNone(headline)

    def test_current_headline(self):
        cats = ["sports","entertainment","tech","politics","health","travel","business"]
        for cat in cats:
            headline = self.cur_svc.get_current_headline(cat)
            self.assertIsNotNone(headline)

class BlurbServicesTestCase(TestCase):
    def setUp(self):
        self.blurb_svc = BlurbServices()

    def test_blurb_score(self):
        Blurb.objects.create(id=0,text="Test blurb")
        blurb = Blurb.objects.get(id=0)
        cats_and_scores = {"sports":.99, "entertainment" : 0.0, "tech" : 0.0, "politics" : 0.0, "health" : 0.0, "business" : 0.0, "travel" : 0.0}
        for cat,score in cats_and_scores.items():
            ScoreVectorNew.objects.create(blurb=blurb,category=cat,score=0.0)

        highest_score_cat = BlurbServices.get_highest_cat_new(blurb)
        self.assertEquals(highest_score_cat, 'sports')

class LanguageServicesTestCase(TestCase):
    def setUp(self):
        self.lang_svc = LanguageServices()

    def test_text_to_speech(self):
        test_text = "This is a speech to text test."
        audio_bytes = self.lang_svc.text_to_speech(test_text, "dummyid")
        self.assertIsNotNone(audio_bytes)









