from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'contest'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES

class setupround(WaitPage):
    pass


class Intro(Page):
    pass


class Decision(WaitPage):
    pass


class decisionwaitpage(WaitPage):
    pass


class Results(WaitPage):
    pass


class Endblock(WaitPage):
    pass




page_sequence = [Intro, Decision, Results,Endblock,]
