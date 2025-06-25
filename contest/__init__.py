from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'contest'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2
    ENDOWMENT = Currency(10)
    COST_PER_TICKET = Currency(0.50)
    PRIZE = Currency(10)


class Subsession(BaseSubsession):
    is_paid = models.BooleanField()
    csf =  models.StringField(Choices=["share", "allpay"])
    def setup_round(self):
        self.is_paid = self.round_number % 2 == 1 # pay odd periods
        self.csf = self.session.config["contest_csf"]
        for group in self.get_groups():
            group.setup_round()

    def compute_outcome(self):
        for group in self.get_groups():
            group.compute_outcome()

class Group(BaseGroup):
    prize = models.CurrencyField()

    def setup_round(self):
        self.prize = C.PRIZE
        for player in self.get_players():
            player.setup_round()

    def compute_outcome_share(self):
        total= sum(player.tickets_purchased for player in self.get_players())
        for player in self.get_players():
            try:
                player.prize_won=player.tickets_purchased/total
            except ZeroDivisionError:
                player.prize_won= 1/len(self.get_players())

    def compute_outcome_allpay(self):
        max_tickets = max(plyer.tickets_purchased for plyer in self.get_players())
        num_tied = len ([player for player in self.get_player()
                         if player.tickets_purchased==max_tickets])
        for player in self.get_players():
            if player.tickets_purchased==max_tickets:
                player.prize_won= 1/num_tied
            else:
                player.prize_won = 0

    def compute_outcome(self):
        if self.subsession.csf == "share":
            self.compute_outcome_share()
        elif self.subsession.csf == "allpay":
            self.compute_outcome_allpay()

        for player in self.get_players():
            player.earnings = (
                player.endowment -
                player.tickets_purchased * player.cost_per_ticket +
                self.prize * player.prize_won
            )


class Player(BasePlayer):
    endowment = models.CurrencyField()
    cost_per_ticket = models.CurrencyField()
    tickets_purchased = models.IntegerField()
    prize_won = models.FloatField()
    earnings = models.CurrencyField()


    def setup_round(self):
        self.endowment = self.session.config.get("contest_endowment",C.ENDOWMENT)
        self.cost_per_ticket = C.COST_PER_TICKET


    @property
    def coplayer(self):
        return self.group.get_player_by_id(3 - self.id_in_group)

    @property
    def max_tickets_affordable(self):
        return int(self.endowment/self.cost_per_ticket)


# PAGES

class SetupRound(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession):
        subsession.setup_round()




class Intro(Page):
    pass



class Decision(Page):
    form_model= "player"
    form_fields = ["tickets_purchased"]

    @staticmethod
    def error_message(player, values):
        if values["tickets purchased"] < 0:
            return " you cannot buy negative amount of tickets"
        if values["tickets purchased"] > player.max_tickets_affordable:
            return (
                f" Buying {values ['tickets_purchased']} tickets would cost "
                f"{player.cost_per_ticket * values['tickets purchased']}" 
                f"which is more than your endowment {player.endowment}.")
        return None





class DecisionWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession):
        subsession.compute_outcome()


class Results(Page):
    pass


class Endblock(WaitPage):
    pass




page_sequence = [
    SetupRound,
    Intro,
    Decision,
    DecisionWaitPage,
    Results,
    Endblock,
]
