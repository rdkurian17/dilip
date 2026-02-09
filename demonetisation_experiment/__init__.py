# demonetisation_experiment/__init__.py

from otree.api import *
import random
import string

doc = """
Demonetisation Experiment: Tax compliance and liquidity shock
"""


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
    TIER_1_THRESHOLD = 70
    TIER_2_THRESHOLD = 140
    TIER_1_AUDIT = 5
    TIER_2_AUDIT = 15
    TIER_3_AUDIT = 30


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    # Assign treatment at round 1 based on session config
    if subsession.round_number == 1:
        treatment = subsession.session.config.get('treatment', 'sudden')
        for p in subsession.get_players():
            p.treatment = treatment
            p.participant.treatment = treatment


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Treatment (assigned automatically in creating_session)
    treatment = models.StringField(initial='')

    # Main decision: allocation
    deposit_decision = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label="How much do you want to deposit in your account?"
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
        label="How much do you want to spend from CASH?"
    )
    spend_from_deposit = models.CurrencyField(initial=0)

    # Cash payment friction
    cash_verification_code = models.StringField(initial='')
    cash_verification_entry = models.StringField(
        blank=True,
        initial='',
        label="Enter the verification code exactly as shown:"
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

    # Post-survey
    age = models.IntegerField(label="Your age:", min=18, max=100, blank=True)
    gender = models.StringField(
        label="Gender:",
        choices=['Male', 'Female', 'Non-binary', 'Prefer not to say'],
        widget=widgets.RadioSelect,
        blank=True
    )
    risk_attitude = models.IntegerField(
        label="How willing are you to take risks?",
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        widget=widgets.RadioSelect,
        blank=True
    )
    trust_government = models.IntegerField(
        label="How much do you trust government institutions?",
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        widget=widgets.RadioSelect,
        blank=True
    )

    # ---------- Helper properties ----------

    @property
    def progress_pct(self):
        return int(self.round_number / C.NUM_ROUNDS * 100)

    # ---------- Helper methods ----------

    def generate_verification_code(self):
        """Generate a 6-character random code (mixed upper/lower/digits)."""
        chars = string.ascii_letters + string.digits
        code = (
            random.choice(string.ascii_uppercase) +
            random.choice(string.ascii_lowercase) +
            random.choice(string.digits) +
            ''.join(random.choices(chars, k=3))
        )
        code_list = list(code)
        random.shuffle(code_list)
        return ''.join(code_list)

    def calculate_personal_audit_rate(self):
        """Audit rate (rounds 8-10) based on how much old cash is converted in round 8."""
        amt = self.conversion_amount or 0
        if amt <= C.TIER_1_THRESHOLD:
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
            self.treatment = prev.treatment
            self.personal_audit_rate = prev.personal_audit_rate
            self.total_tax_paid = prev.total_tax_paid
            self.total_fines_paid = prev.total_fines_paid

        # ALWAYS set these safety defaults for every round
        self.was_audited = False
        self.fine_paid = cu(0)
        self.tax_evaded_found = cu(0)
        self.random_draw = 0
        self.audit_probability = 0

        # Set personal_audit_rate for round 1
        if self.round_number == 1:
            self.personal_audit_rate = C.BASE_AUDIT_PROB
            self.total_tax_paid = cu(0)
            self.total_fines_paid = cu(0)


# ---------------- PAGES ----------------

class Consent(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            qualtrics_link=player.session.config.get('consent_link', 'https://your-qualtrics-link-here.com')
        )


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # treatment will be assigned by creating_session in round 1
        return dict(
            treatment=player.treatment,
            show_shock_warning=(player.treatment == 'preannounced'),
        )


class ComprehensionQuiz(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1
    # Informational-only page in your HTML (no form fields).


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
    def vars_for_template(player: Player):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        return dict(
            old_cash=prev.total_cash,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Load cumulative balances for this round
        player.carry_forward()

        prev = player.in_round(C.SHOCK_ROUND - 1)
        old_cash = prev.total_cash

        converted = min(player.conversion_amount or 0, old_cash)
        player.cash_lost = old_cash - converted

        # Conversion moves old cash into deposit (no tax on conversion), and wipes cash
        player.total_deposit += converted
        player.total_cash = 0

        # Set elevated audit rate for rounds 8-10
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
        # In round 8 (non-baseline), totals have already been updated by ConversionDecision.
        if player.round_number == C.SHOCK_ROUND and player.treatment != 'baseline':
            current_deposit = player.total_deposit
            current_cash = player.total_cash
        else:
            prev = player.in_round(player.round_number - 1) if player.round_number > 1 else None
            current_deposit = prev.total_deposit if prev else 0
            current_cash = prev.total_cash if prev else 0

        if player.round_number < C.SHOCK_ROUND:
            phase = f"Pre-shock Phase: Round {player.round_number}/7"
        elif player.round_number <= C.ELEVATED_AUDIT_END:
            phase = f"Elevated Audit Phase: Round {player.round_number}/10"
        else:
            phase = f"Normal Phase: Round {player.round_number}/15"

        audit_prob = player.get_audit_probability() if player.round_number > 1 else C.BASE_AUDIT_PROB

        return dict(
            round_num=player.round_number,
            phase=phase,
            current_deposit=current_deposit,
            current_cash=current_cash,
            audit_prob=audit_prob,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # For normal rounds carry-forward here.
        # For round 8 non-baseline, carry-forward already happened in ConversionDecision.
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
    form_fields = ['spend_from_cash', 'cash_verification_entry']

    @staticmethod
    def vars_for_template(player: Player):
        if not player.cash_verification_code:
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

        if spend_cash < 0:
            return 'Cannot spend a negative amount.'

        if spend_cash > player.cash_before_spending:
            return f'Not allowable amount. You only have {player.cash_before_spending} ECU in cash.'

        spend_deposit = C.MANDATORY_SPENDING - spend_cash
        if spend_deposit < 0:
            return f'You must spend exactly {C.MANDATORY_SPENDING} ECU. Cash spending cannot exceed this.'

        if spend_deposit > player.deposit_before_spending:
            return f'Not allowable amount. You need {spend_deposit} ECU from deposit but only have {player.deposit_before_spending} ECU.'

        if spend_cash > 0:
            entered_code = (values.get('cash_verification_entry') or '').strip()
            if entered_code != player.cash_verification_code:
                return 'Verification code does not match. Please enter the code exactly as shown (case-sensitive).'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        spend_cash = player.spend_from_cash or 0
        player.spend_from_deposit = C.MANDATORY_SPENDING - spend_cash

        player.total_deposit -= player.spend_from_deposit
        player.total_cash -= spend_cash

        player.audit_probability = player.get_audit_probability()


class AuditOutcome(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.random_draw = random.randint(1, 100)

        if player.random_draw <= (player.audit_probability or 0):
            player.was_audited = True

            evaded_tax = player.total_cash * C.TAX_RATE
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

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            was_audited=player.was_audited,
            random_draw=player.random_draw,
            audit_threshold=player.audit_probability,
            tax_evaded=player.tax_evaded_found,
            fine=player.fine_paid,
            cash_balance=player.total_cash,
            round_num=player.round_number,
            progress_pct=player.progress_pct,
        )


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
    form_fields = ['age', 'gender', 'risk_attitude', 'trust_government']

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
        real_payment = total_wealth * exchange_rate

        player.payoff = total_wealth

        return dict(
            final_deposit=player.total_deposit,
            final_cash=player.total_cash,
            total_wealth=total_wealth,
            total_tax_paid=player.total_tax_paid,
            total_fines_paid=player.total_fines_paid,
            real_payment=real_payment,
        )


page_sequence = [
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
    FinalResults,
]
