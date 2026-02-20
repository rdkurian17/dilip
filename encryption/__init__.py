from otree.api import (
    BaseConstants,
    BaseGroup,
    BasePlayer,
    BaseSubsession,
    Page,
)

doc = """
Encryption real-effort task
"""


class C(BaseConstants):
    NAME_IN_URL = "encryption"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class Intro(Page):
    pass


page_sequence = [
    Intro,
]
