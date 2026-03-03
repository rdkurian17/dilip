from otree.api import *
import random
import string

doc = """
Demonetisation Experiment: Tax compliance and liquidity shock
"""

# Module-level constant --- safe to reference inside Player field definitions
LIKERT_CHOICES = [
    [1, "Strongly Disagree"],
    [2, "Disagree"],
    [3, "Somewhat Disagree"],
    [4, "Neither Agree nor Disagree"],
    [5, "Somewhat Agree"],
    [6, "Agree"],
    [7, "Strongly Agree"],
]

# HEXACO Honesty-Humility uses a 5-point scale
HEXACO_CHOICES = [
    [1, "Strongly Disagree"],
    [2, "Disagree"],
    [3, "Neutral"],
    [4, "Agree"],
    [5, "Strongly Agree"],
]


class C(BaseConstants):
    NAME_IN_URL = 'demonetisation_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 15

    # Economic parameters
    ENDOWMENT = cu(100)
    TAX_RATE = 0.30
    MANDATORY_SPENDING = cu(40)
    BASE_AUDIT_PROB = 5  # out of 100
    FINE_MULTIPLIER = 2  # fine = 2x unpaid tax; total penalty = tax + fine = 3x tax

    # Shock timing
    SHOCK_ROUND = 8
    ELEVATED_AUDIT_END = 10

    # Audit probability tiers based on conversion amount
    TIER_1_THRESHOLD = 50   # 1-50 ECU
    TIER_2_THRESHOLD = 100  # 51-100 ECU
    TIER_1_AUDIT = 10       # 1-50: 10%
    TIER_2_AUDIT = 15       # 51-100: 15%
    TIER_3_AUDIT = 20       # >100: 20%


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    treatment = subsession.session.config.get('treatment', 'sudden')
    for p in subsession.get_players():
        if subsession.round_number == 1:
            p.treatment = treatment
            p.participant.vars['treatment'] = treatment
        else:
            p.treatment = p.participant.vars.get('treatment', treatment)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Treatment (assigned automatically in creating_session)
    treatment = models.StringField(initial='')

    # Main decision: allocation
    deposit_decision = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label="Amount to deposit:"
    )

    # Calculated amounts after allocation
    cash_kept = models.CurrencyField(initial=0)
    tax_paid_this_round = models.CurrencyField(initial=0)
    deposit_after_tax = models.CurrencyField(initial=0)

    # Balances BEFORE spending (snapshots used for display/validation)
    deposit_before_spending = models.CurrencyField(initial=0)
    cash_before_spending = models.CurrencyField(initial=0)

    # Spending decisions
    spend_from_cash = models.CurrencyField(
        min=0,
        initial=0,
        label="Amount to spend from cash:"
    )
    spend_from_deposit = models.CurrencyField(
        min=0,
        initial=0,
        label="Amount to spend from deposit:"
    )

    # Cash payment friction
    cash_verification_code = models.StringField(initial='')
    cash_verification_entry = models.StringField(
        blank=True,
        initial='',
        label="Type the code exactly as shown to confirm cash payment:"
    )

    # Cumulative balances (carried forward)
    total_deposit = models.CurrencyField(initial=0)
    total_cash = models.CurrencyField(initial=0)

    # Round 8 conversion
    conversion_amount = models.CurrencyField(min=0, initial=0)
    cash_lost = models.CurrencyField(initial=0)

    # Audit (safe defaults to avoid None errors)
    audit_probability = models.IntegerField(initial=0)
    random_draw = models.IntegerField(initial=0)
    was_audited = models.BooleanField(initial=False)
    fine_paid = models.CurrencyField(initial=0)
    tax_evaded_found = models.CurrencyField(initial=0)
    personal_audit_rate = models.IntegerField(initial=C.BASE_AUDIT_PROB)

    # Cumulative tracking
    total_tax_paid = models.CurrencyField(initial=0)
    total_fines_paid = models.CurrencyField(initial=0)

    # -------------------------------------------------------
    # Consent page: participant identification
    # -------------------------------------------------------
    participant_full_name = models.StringField(label="Full name:")
    participant_email = models.StringField(label="Email address:")
    seat_number = models.StringField(label="Seat / PC number:")

    # Post-survey: Demographics & trust (PostSurvey page)
    # -------------------------------------------------------
    participant_name = models.StringField(label="Your name:", blank=True)
    age = models.IntegerField(label="Your age:", min=18, max=100)
    gender = models.StringField(
        label="Gender:",
        choices=[
            ['Male', 'Male'],
            ['Female', 'Female'],
            ['Non-binary', 'Non-binary'],
            ['Prefer not to say', 'Prefer not to say'],
        ],
        widget=widgets.RadioSelect,
    )
    risk_attitude = models.IntegerField(
        label="How willing are you to take risks?",
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        widget=widgets.RadioSelect,
    )
    trust_government = models.IntegerField(
        label="How much do you trust government institutions?",
        min=0, max=10,
    )

    # -------------------------------------------------------
    # Tax Morale - WVS single item (1-10 scale)
    # On PostSurvey page, displayed as horizontal slider
    # -------------------------------------------------------
    tax_morale = models.IntegerField(
        label="Cheating on taxes if you have a chance.",
        min=1, max=10,
    )

    # -------------------------------------------------------
    # Risk preference (Eckel-Grossman task) - RiskTaskEG page
    # -------------------------------------------------------
    eg_choice = models.IntegerField(
        choices=[
            [1, "Option 1"],
            [2, "Option 2"],
            [3, "Option 3"],
            [4, "Option 4"],
            [5, "Option 5"],
            [6, "Option 6"],
        ],
        widget=widgets.RadioSelect,
        label="Please choose ONE option.",
    )
    eg_risk_type = models.StringField(initial='')

    # -------------------------------------------------------
    # Loss Aversion Scale - Li et al. (2021)
    # 8 items, 7-point scale; items 5 & 8 are reverse coded
    # -------------------------------------------------------
    loss_1 = models.IntegerField(
        label="When making a decision, I think much more about what might be lost than what might be gained.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_2 = models.IntegerField(
        label="The pain of losing money matters more than the pleasure of gaining the same amount of money.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_3 = models.IntegerField(
        label="I feel nervous when I have to make a decision that may lead to loss.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_4 = models.IntegerField(
        label="The pain from losing something matters much more to me than the pleasure from getting it.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_5 = models.IntegerField(
        label="Avoiding failure is less important to me than seeking success.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_6 = models.IntegerField(
        label="Experiencing a major loss stays in my mind longer than experiencing a major gain.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_7 = models.IntegerField(
        label="A potential failure scares me more than a potential success encourages me.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )
    loss_8 = models.IntegerField(
        label="The suffering that comes with losses can be fully offset by the pleasure that comes from gains.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    # -------------------------------------------------------
    # HEXACO-60 Honesty-Humility - 10 items, 5-point scale
    # Page class is named RuleBreaking; HTML file is RuleBreaking.html
    # -------------------------------------------------------
    hh_1 = models.IntegerField(
        label="I wouldn't use flattery to get a raise or promotion at work.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_2 = models.IntegerField(
        label="I'm interested in making money primarily to have a luxurious lifestyle.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_3 = models.IntegerField(
        label="I wouldn't pretend to like someone just to get that person to do favors for me.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_4 = models.IntegerField(
        label="I'd get a lot of pleasure from owning expensive luxury goods.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_5 = models.IntegerField(
        label="I wouldn't feel bad about taking a bribe if it was very large.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_6 = models.IntegerField(
        label="I would be tempted to buy stolen property if I were financially tight.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_7 = models.IntegerField(
        label="I am an ordinary person who is no better than others.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_8 = models.IntegerField(
        label="I think that I am entitled to more respect than the average person is.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_9 = models.IntegerField(
        label="I wouldn't want people to treat me as though I were superior to them.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )
    hh_10 = models.IntegerField(
        label="I would like to know how to make lots of money in a dishonest manner.",
        choices=HEXACO_CHOICES,
        widget=widgets.RadioSelect,
    )

    # Comprehension quiz
    quiz_q1 = models.StringField(blank=True, initial='', label="Your answer:")
    quiz_q2 = models.StringField(blank=True, initial='', label="Your answer:")
    quiz_q3 = models.StringField(blank=True, initial='', label="Your answer:")

    # ---------- Helper properties ----------

    @property
    def progress_pct(self):
        return int(self.round_number / C.NUM_ROUNDS * 100)

    # ---------- Helper methods ----------

    def generate_verification_code(self):
        """Generate a random code mixing letters and numbers."""
        code_parts = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
        ]
        random.shuffle(code_parts)
        return ''.join(code_parts)

    def calculate_personal_audit_rate(self):
        """Audit rate (rounds 8-10) based on how much old cash is converted in round 8."""
        amt = self.conversion_amount or 0
        if amt == 0:
            return C.BASE_AUDIT_PROB
        elif amt <= C.TIER_1_THRESHOLD:
            return C.TIER_1_AUDIT
        elif amt <= C.TIER_2_THRESHOLD:
            return C.TIER_2_AUDIT
        else:
            return C.TIER_3_AUDIT

    def get_audit_probability(self):
        """Audit probability for this round."""
        if self.treatment == 'baseline':
            return C.BASE_AUDIT_PROB
        if self.round_number < C.SHOCK_ROUND:
            return C.BASE_AUDIT_PROB
        elif self.round_number <= C.ELEVATED_AUDIT_END:
            return self.personal_audit_rate
        else:
            return C.BASE_AUDIT_PROB

    def carry_forward(self):
        """Copy cumulative state from previous round into this round."""
        if self.round_number > 1:
            prev = self.in_round(self.round_number - 1)
            self.total_deposit = prev.total_deposit
            self.total_cash = prev.total_cash
            self.personal_audit_rate = prev.personal_audit_rate
            self.total_tax_paid = prev.total_tax_paid
            self.total_fines_paid = prev.total_fines_paid
            # Carry conversion_amount forward through rounds 8-10 so the
            # auditable base (cash + converted amount) is correct during the
            # elevated window. After round 10 conversion_amount is not carried
            # forward so converted money becomes safe from round 11 onwards.
            if self.round_number <= C.ELEVATED_AUDIT_END:
                self.conversion_amount = prev.conversion_amount

        self.treatment = self.participant.vars.get('treatment', self.treatment or '')
        self.was_audited = False
        self.fine_paid = cu(0)
        self.tax_evaded_found = cu(0)
        self.random_draw = 0
        self.audit_probability = 0

        if self.round_number == 1:
            self.personal_audit_rate = C.BASE_AUDIT_PROB
            self.total_tax_paid = cu(0)
            self.total_fines_paid = cu(0)


# -------------- PAGES --------------

class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class ParticipantInfo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Consent(Page):
    form_model = 'player'
    form_fields = ['participant_full_name', 'participant_email', 'seat_number']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            treatment=player.treatment,
            show_shock_warning=(player.treatment == 'preannounced'),
            show_may_shock=(player.treatment in ['baseline', 'sudden']),
        )


class ComprehensionQuiz(Page):
    form_model = 'player'
    form_fields = ['quiz_q1', 'quiz_q2', 'quiz_q3']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            correct_q1='70',
            correct_q2='45',
            correct_q3='5',
        )


class ShockAnnouncement(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline')

    @staticmethod
    def vars_for_template(player: Player):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        return dict(
            old_cash=prev.total_cash,
            current_deposit=prev.total_deposit,
            is_sudden=(player.treatment == 'sudden'),
            progress_pct=player.progress_pct,
        )


class ConversionDecision(Page):
    form_model = 'player'
    form_fields = ['conversion_amount']

    @staticmethod
    def is_displayed(player: Player):
        return (player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline')

    @staticmethod
    def conversion_amount_max(player: Player):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        return prev.total_cash

    @staticmethod
    def error_message(player: Player, values):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        old_cash = prev.total_cash
        conversion = values.get('conversion_amount') or 0
        if conversion < 0:
            return 'Cannot convert a negative amount.'
        if conversion > old_cash:
            return f'The entered amount ({conversion} ECU) is greater than your cash in hand ({old_cash} ECU). Please enter an amount less than or equal to {old_cash} ECU.'

    @staticmethod
    def vars_for_template(player: Player):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        return dict(
            old_cash=prev.total_cash,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.carry_forward()
        prev = player.in_round(C.SHOCK_ROUND - 1)
        old_cash = prev.total_cash
        converted = min(player.conversion_amount or 0, old_cash)
        player.cash_lost = old_cash - converted
        player.total_deposit += converted
        player.total_cash = 0
        player.personal_audit_rate = player.calculate_personal_audit_rate()


class ConversionOutcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline')

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            converted=player.conversion_amount or 0,
            lost=player.cash_lost,
            new_audit_rate=player.personal_audit_rate,
            new_deposit=player.total_deposit,
            progress_pct=player.progress_pct,
        )


class AllocationDecision(Page):
    form_model = 'player'
    form_fields = ['deposit_decision']

    @staticmethod
    def vars_for_template(player: Player):
        if player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline':
            current_deposit = player.total_deposit
            current_cash = player.total_cash
            audit_prob = player.get_audit_probability()
        else:
            prev = player.in_round(player.round_number - 1) if player.round_number > 1 else None
            current_deposit = prev.total_deposit if prev else 0
            current_cash = prev.total_cash if prev else 0
            if player.round_number > 1:
                if player.round_number <= C.ELEVATED_AUDIT_END and player.treatment != 'baseline' and player.round_number > C.SHOCK_ROUND:
                    audit_prob = prev.personal_audit_rate
                else:
                    audit_prob = player.get_audit_probability()
            else:
                audit_prob = C.BASE_AUDIT_PROB

        return dict(
            round_num=player.round_number,
            current_deposit=current_deposit,
            current_cash=current_cash,
            audit_prob=audit_prob,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if not (player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline'):
            player.carry_forward()
        deposited = player.deposit_decision or 0
        player.cash_kept = C.ENDOWMENT - deposited
        player.tax_paid_this_round = deposited * C.TAX_RATE
        player.deposit_after_tax = deposited - player.tax_paid_this_round
        player.total_deposit += player.deposit_after_tax
        player.total_cash += player.cash_kept
        player.total_tax_paid += player.tax_paid_this_round
        player.deposit_before_spending = player.total_deposit
        player.cash_before_spending = player.total_cash


class AllocationResult(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            round_num=player.round_number,
            deposited=player.deposit_decision,
            tax_paid=player.tax_paid_this_round,
            deposit_added=player.deposit_after_tax,
            cash_kept=player.cash_kept,
            new_deposit=player.deposit_before_spending,
            new_cash=player.cash_before_spending,
            progress_pct=player.progress_pct,
        )


class SpendingDecision(Page):
    form_model = 'player'
    form_fields = ['spend_from_cash', 'spend_from_deposit', 'cash_verification_entry']

    @staticmethod
    def vars_for_template(player: Player):
        player.cash_verification_code = player.generate_verification_code()
        return dict(
            round_num=player.round_number,
            deposit_balance=player.deposit_before_spending,
            cash_balance=player.cash_before_spending,
            verification_code=player.cash_verification_code,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def error_message(player: Player, values):
        spend_cash = values.get('spend_from_cash') or 0
        spend_deposit = values.get('spend_from_deposit') or 0
        if spend_cash < 0:
            return 'Cannot spend a negative amount from cash.'
        if spend_deposit < 0:
            return 'Cannot spend a negative amount from deposit.'
        total_spent = spend_cash + spend_deposit
        if total_spent != C.MANDATORY_SPENDING:
            return f'The sum of cash and deposit spending must equal exactly {C.MANDATORY_SPENDING} ECU. Currently you have {total_spent} ECU.'
        if spend_cash > player.cash_before_spending:
            return f'Not enough cash. You only have {player.cash_before_spending} ECU in cash but are trying to spend {spend_cash} ECU.'
        if spend_deposit > player.deposit_before_spending:
            return f'Not enough in deposit. You only have {player.deposit_before_spending} ECU in deposit but are trying to spend {spend_deposit} ECU.'
        if spend_cash > 0:
            entered_code = (values.get('cash_verification_entry') or '').strip()
            if entered_code != player.cash_verification_code:
                return 'You must type the verification code exactly as shown (case-sensitive) to confirm your cash payment.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        spend_cash = player.spend_from_cash or 0
        spend_deposit = player.spend_from_deposit or 0
        player.total_deposit -= spend_deposit
        player.total_cash -= spend_cash
        player.audit_probability = player.get_audit_probability()
        player.random_draw = random.randint(1, 100)


class AuditOutcome(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # FIX: vars_for_template runs BEFORE before_next_page, so was_audited
        # is always False when the page renders. We compute the result here
        # directly from random_draw vs audit_probability so the page shows
        # the correct outcome. before_next_page still does all the accounting.
        audited = player.random_draw <= (player.audit_probability or 0)
        # During the elevated audit window (rounds 8-10), the auditable base
        # includes both cash in hand AND the amount converted at the shock.
        # From round 11 onwards, converted money is safe; only cash is at risk.
        in_elevated_window = (
            player.treatment != 'baseline'
            and C.SHOCK_ROUND <= player.round_number <= C.ELEVATED_AUDIT_END
        )
        converted = player.conversion_amount or 0
        auditable_base = player.total_cash + (converted if in_elevated_window else cu(0))
        if audited:
            evaded_tax = auditable_base * C.TAX_RATE
            total_penalty = evaded_tax + (evaded_tax * C.FINE_MULTIPLIER)
        else:
            evaded_tax = cu(0)
            total_penalty = cu(0)
        return dict(
            was_audited=audited,
            random_draw=player.random_draw,
            audit_threshold=player.audit_probability,
            tax_evaded=evaded_tax,
            fine=total_penalty,
            cash_balance=player.total_cash,
            converted_at_risk=converted if in_elevated_window else cu(0),
            round_num=player.round_number,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        in_elevated_window = (
            player.treatment != 'baseline'
            and C.SHOCK_ROUND <= player.round_number <= C.ELEVATED_AUDIT_END
        )
        converted = player.conversion_amount or 0
        auditable_base = player.total_cash + (converted if in_elevated_window else cu(0))

        if player.random_draw <= (player.audit_probability or 0):
            player.was_audited = True
            evaded_tax = auditable_base * C.TAX_RATE
            fine_only = evaded_tax * C.FINE_MULTIPLIER
            total_penalty = evaded_tax + fine_only
            player.tax_evaded_found = evaded_tax
            player.fine_paid = total_penalty
            player.total_fines_paid += total_penalty
            if player.total_deposit >= total_penalty:
                player.total_deposit -= total_penalty
            else:
                remaining = total_penalty - player.total_deposit
                player.total_deposit = 0
                player.total_cash = max(cu(0), player.total_cash - remaining)
        else:
            player.was_audited = False
            player.fine_paid = 0
            player.tax_evaded_found = 0


class RoundSummary(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            round_num=player.round_number,
            deposited=player.deposit_decision,
            tax_paid=player.tax_paid_this_round,
            kept_cash=player.cash_kept,
            spent_cash=player.spend_from_cash,
            spent_deposit=player.spend_from_deposit,
            was_audited=player.field_maybe_none('was_audited') or False,
            fine_paid=player.fine_paid,
            final_deposit=player.total_deposit,
            final_cash=player.total_cash,
            total_tax=player.total_tax_paid,
            total_fines=player.total_fines_paid,
            progress_pct=player.progress_pct,
        )


class PostSurvey(Page):
    form_model = 'player'
    form_fields = ['participant_name', 'age', 'gender', 'trust_government', 'tax_morale']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class RiskTaskEG(Page):
    form_model = 'player'
    form_fields = ['eg_choice']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        c = player.eg_choice or 0
        if c in [1, 2]:
            player.eg_risk_type = 'risk_averse'
        elif c in [3, 4]:
            player.eg_risk_type = 'risk_neutral_or_moderate'
        elif c in [5, 6]:
            player.eg_risk_type = 'risk_seeking'

    @staticmethod
    def vars_for_template(player: Player):
        lotteries = [
            dict(opt=1, low=cu(40), high=cu(40)),
            dict(opt=2, low=cu(32), high=cu(48)),
            dict(opt=3, low=cu(24), high=cu(56)),
            dict(opt=4, low=cu(16), high=cu(64)),
            dict(opt=5, low=cu(8), high=cu(72)),
            dict(opt=6, low=cu(0), high=cu(80)),
        ]
        return dict(lotteries=lotteries)


class LossAversion(Page):
    """Loss Aversion Scale - Li et al. (2021), 8 items, 7-point scale."""
    form_model = 'player'
    form_fields = ['loss_1', 'loss_2', 'loss_3', 'loss_4', 'loss_5', 'loss_6', 'loss_7', 'loss_8']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class RuleBreaking(Page):
    """HEXACO-60 Honesty-Humility subscale - 10 items, 5-point scale.
    HTML file: RuleBreaking.html  |  Fields: hh_1 to hh_10"""
    form_model = 'player'
    form_fields = ['hh_1', 'hh_2', 'hh_3', 'hh_4', 'hh_5', 'hh_6', 'hh_7', 'hh_8', 'hh_9', 'hh_10']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        total_wealth = player.total_deposit + player.total_cash
        exchange_rate = player.session.config.get('real_world_currency_per_point', 0.01)
        real_payment = float(total_wealth) * exchange_rate
        player.payoff = total_wealth
        return dict(
            final_deposit=player.total_deposit,
            final_cash=player.total_cash,
            total_wealth=total_wealth,
            real_payment=f"{real_payment:.2f}",
        )


page_sequence = [
    Welcome,
    ParticipantInfo,
    Consent,
    Instructions,
    ComprehensionQuiz,
    ShockAnnouncement,
    ConversionDecision,
    ConversionOutcome,
    AllocationDecision,
    AllocationResult,
    SpendingDecision,
    AuditOutcome,
    RoundSummary,
    PostSurvey,
    RiskTaskEG,
    LossAversion,
    RuleBreaking,
    FinalResults,
]