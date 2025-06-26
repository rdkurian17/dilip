import random

from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'contest'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2
    NUM_PAID_ROUNDS = 1
    ENDOWMENT = Currency(10)
    COST_PER_TICKET = Currency(0.50)
    PRIZE = Currency(8)


class Subsession(BaseSubsession):
    is_paid = models.BooleanField(initial=False)
    csf = models.StringField(choices=["share", "allpay", "lottery"])

    def setup_round(self):
        if self.round_number == 1:
            self.setup_paid_rounds()
        self.csf = self.session.config["contest_csf"]
        if self.session.config.get("contest_group_randomly", False):
            self.group_randomly()
        for group in self.get_groups():
            group.setup_round()

    def setup_paid_rounds(self):
        for rd in random.sample(self.in_rounds(1, C.NUM_ROUNDS),
                                k=C.NUM_PAID_ROUNDS):
            rd.is_paid = True

    def compute_outcome(self):
        for group in self.get_groups():
            group.compute_outcome()


class Group(BaseGroup):
    prize = models.CurrencyField()

    def setup_round(self):
        self.prize = C.PRIZE
        for player in self.get_players():
            player.setup_round()

    def compute_outcome_lottery(self):
        try:
            winner = random.choices(self.get_players(), k=1,
                                    weights=[p.tickets_purchased for p in self.get_players()])[0]
        except ValueError:
            winner = random.choice(self.get_players())
        for player in self.get_players():
            player.prize_won = 1 if player == winner else 0

    def compute_outcome_share(self):
        total = sum(player.tickets_purchased for player in self.get_players())
        for player in self.get_players():
            try:
                player.prize_won = player.tickets_purchased / total
            except ZeroDivisionError:
                player.prize_won = 1 / len(self.get_players())

    def compute_outcome_allpay(self):
        max_tickets = max(player.tickets_purchased for player in self.get_players())
        num_tied = len([player for player in self.get_players()
                        if player.tickets_purchased == max_tickets])
        for player in self.get_players():
            if player.tickets_purchased == max_tickets:
                player.prize_won = 1 / num_tied
            else:
                player.prize_won = 0

    def compute_outcome(self):
        if self.subsession.csf == "share":
            self.compute_outcome_share()
        elif self.subsession.csf == "allpay":
            self.compute_outcome_allpay()
        elif self.subsession.csf == "lottery":
            self.compute_outcome_lottery()
        for player in self.get_players():
            player.earnings = (
                player.endowment -
                player.tickets_purchased * player.cost_per_ticket +
                self.prize * player.prize_won
            )
            if self.subsession.is_paid:
                player.payoff = player.earnings


class Player(BasePlayer):
    endowment = models.CurrencyField()
    cost_per_ticket = models.CurrencyField()
    tickets_purchased = models.IntegerField()
    prize_won = models.FloatField()
    earnings = models.CurrencyField()

    def setup_round(self):
        self.endowment = self.session.config.get("contest_endowment", C.ENDOWMENT)
        self.cost_per_ticket = C.COST_PER_TICKET

    @property
    def coplayer(self):
        return self.group.get_player_by_id(3 - self.id_in_group)

    @property
    def max_tickets_affordable(self):
        return int(self.endowment / self.cost_per_ticket)

    def in_paid_rounds(self):
        return [rd for rd in self.in_all_rounds() if rd.subsession.is_paid]


# PAGES
class SetupRound(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession):
        subsession.setup_round()


class Intro(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Decision(Page):
    form_model = "player"
    form_fields = ["tickets_purchased"]

    @staticmethod
    def error_message(player, values):
        if values["tickets_purchased"] < 0:
            return "You cannot buy a negative number of tickets."
        if values["tickets_purchased"] > player.max_tickets_affordable:
            return (
                f"Buying {values['tickets_purchased']} tickets would cost "
                f"{values['tickets_purchased'] * player.cost_per_ticket} "
                f"which is more than your endowment of {player.endowment}."
            )
        return None


class DecisionWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession):
        subsession.compute_outcome()


class Results(Page):
    pass


class EndBlock(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [
    SetupRound,
    Intro,
    Decision,
    DecisionWaitPage,
    Results,
    EndBlock,
]