# demonetisation_experiment/__init__.py

from otree.api import *
import random
import string

doc = """
Demonetisation Experiment: Tax compliance and liquidity shock
"""

# Module-level constant — safe to reference inside Player field definitions
LIKERT_CHOICES = [
    [1, "Strongly Disagree"],
    [2, "Disagree"],
    [3, "Somewhat Disagree"],
    [4, "Neither Agree nor Disagree"],
    [5, "Somewhat Agree"],
    [6, "Agree"],
    [7, "Strongly Agree"],
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

    # Audit probability tiers based on conversion amount (UPDATED)
    TIER_1_THRESHOLD = 50  # 1-50 ECU
    TIER_2_THRESHOLD = 100  # 51-100 ECU
    TIER_1_AUDIT = 10  # 1-50: 10%
    TIER_2_AUDIT = 15  # 51-100: 15%
    TIER_3_AUDIT = 20  # >100: 20%


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    # oTree calls creating_session for every round at session start.
    # participant.vars persists across rounds, so we use it to carry treatment safely.
    treatment = subsession.session.config.get('treatment', 'sudden')
    for p in subsession.get_players():
        if subsession.round_number == 1:
            # Set treatment on round 1 and store in participant.vars for other rounds
            p.treatment = treatment
            p.participant.vars['treatment'] = treatment
        else:
            # Read from participant.vars — always available regardless of round order
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

    # Spending decisions (UPDATED: two separate fields)
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

    # Post-survey (original fields)
    age = models.IntegerField(label="Your age:", min=18, max=100, blank=True)
    gender = models.StringField(
        label="Gender:",
        choices=[
            ['Male', 'Male'],
            ['Female', 'Female'],
            ['Non-binary', 'Non-binary'],
            ['Prefer not to say', 'Prefer not to say'],
        ],
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

    # NEW POST-SURVEY FIELDS
    # Risk preference (Eckel–Grossman task)
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
        blank=True
    )
    eg_risk_type = models.StringField(initial='')

    # Loss Aversion
    loss_1 = models.IntegerField(
        label="I am more sensitive to losses than to gains.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    loss_2 = models.IntegerField(
        label="Avoiding losses is more important to me than achieving gains.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    loss_3 = models.IntegerField(
        label="Losses affect me more strongly than equal-sized gains.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )

    # Rule-Breaking Aversion
    rule_1 = models.IntegerField(
        label="Rules should be followed even when enforcement is weak.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    rule_2 = models.IntegerField(
        label="It is acceptable to ignore rules if no one is harmed.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    rule_3 = models.IntegerField(
        label="I feel guilty when I violate formal rules.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )

    # Liquidity Preference
    liq_1 = models.IntegerField(
        label="I prefer keeping money in liquid form rather than locked away.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    liq_2 = models.IntegerField(
        label="I feel safer when I have cash available.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    liq_3 = models.IntegerField(
        label="Having immediate access to money is very important to me.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )

    # Tax Morale
    tax_1 = models.IntegerField(
        label="Paying taxes is a civic duty.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    tax_2 = models.IntegerField(
        label="Cheating on taxes is morally wrong even if the chance of being caught is small.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    tax_3 = models.IntegerField(
        label="People should pay taxes even if enforcement is weak.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
    )
    tax_4 = models.IntegerField(
        label="It is justifiable to cheat on taxes if you have the chance.",
        choices=LIKERT_CHOICES,
        widget=widgets.RadioSelect,
        blank=True
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
        """Generate a random code mixing letters and numbers (cannot be copy-pasted due to case sensitivity)."""
        # Mix uppercase, lowercase, and digits to create a code that's harder to type
        chars = string.ascii_letters + string.digits
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
        """Audit rate (rounds 8-10) based on how much old cash is converted in round 8. UPDATED."""
        amt = self.conversion_amount or 0
        if amt <= C.TIER_1_THRESHOLD:  # 1-50
            return C.TIER_1_AUDIT  # 10%
        elif amt <= C.TIER_2_THRESHOLD:  # 51-100
            return C.TIER_2_AUDIT  # 15%
        else:  # >100
            return C.TIER_3_AUDIT  # 20%

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

        # Always keep treatment in sync with participant.vars (set by creating_session)
        self.treatment = self.participant.vars.get('treatment', self.treatment or '')

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

class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class ParticipantInfo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Consent(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


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

        audit_prob = player.get_audit_probability() if player.round_number > 1 else C.BASE_AUDIT_PROB

        return dict(
            round_num=player.round_number,
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
    form_fields = ['spend_from_cash', 'spend_from_deposit', 'cash_verification_entry']

    @staticmethod
    def vars_for_template(player: Player):
        # Generate a fresh verification code each time the page loads
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

        # Check for negative amounts
        if spend_cash < 0:
            return 'Cannot spend a negative amount from cash.'
        if spend_deposit < 0:
            return 'Cannot spend a negative amount from deposit.'

        # Check if sum equals mandatory spending
        total_spent = spend_cash + spend_deposit
        if total_spent != C.MANDATORY_SPENDING:
            return f'The sum of cash and deposit spending must equal exactly {C.MANDATORY_SPENDING} ECU. Currently you have {total_spent} ECU.'

        # Check if sufficient balance in each account
        if spend_cash > player.cash_before_spending:
            return f'Not enough cash. You only have {player.cash_before_spending} ECU in cash but are trying to spend {spend_cash} ECU.'

        if spend_deposit > player.deposit_before_spending:
            return f'Not enough in deposit. You only have {player.deposit_before_spending} ECU in deposit but are trying to spend {spend_deposit} ECU.'

        # If spending any cash, require verification code
        if spend_cash > 0:
            entered_code = (values.get('cash_verification_entry') or '').strip()
            if entered_code != player.cash_verification_code:
                return f'You must type the verification code exactly as shown (case-sensitive) to confirm your cash payment.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        spend_cash = player.spend_from_cash or 0
        spend_deposit = player.spend_from_deposit or 0

        player.total_deposit -= spend_deposit
        player.total_cash -= spend_cash

        player.audit_probability = player.get_audit_probability()

        # Generate random draw for audit HERE so it's available on AuditOutcome page
        player.random_draw = random.randint(1, 100)


class AuditOutcome(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Random draw was already generated in SpendingDecision.before_next_page
        # Now we just process the audit result

        # UPDATED: audit happens if random_draw <= audit_probability
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
    form_model = 'player'
    form_fields = ['loss_1', 'loss_2', 'loss_3']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class RuleBreaking(Page):
    form_model = 'player'
    form_fields = ['rule_1', 'rule_2', 'rule_3']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class LiquidityPreference(Page):
    form_model = 'player'
    form_fields = ['liq_1', 'liq_2', 'liq_3']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class TaxMorale(Page):
    form_model = 'player'
    form_fields = ['tax_1', 'tax_2', 'tax_3', 'tax_4']

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
    LiquidityPreference,
    TaxMorale,
    FinalResults,
]