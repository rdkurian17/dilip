from otree.api import *
import random
import string

doc = """Demonetisation Experiment: Tax compliance and liquidity shock"""

LIKERT_CHOICES = [
    [1, "Strongly Disagree"],
    [2, "Disagree"],
    [3, "Somewhat Disagree"],
    [4, "Neither Agree nor Disagree"],
    [5, "Somewhat Agree"],
    [6, "Agree"],
    [7, "Strongly Agree"],
]

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
    NUM_ROUNDS = 17
    ENDOWMENT = cu(100)
    TAX_RATE = 0.30
    MANDATORY_SPENDING = cu(40)
    BASE_AUDIT_PROB = 5
    FINE_MULTIPLIER = 2
    SHOCK_ROUND = 8
    ELEVATED_AUDIT_END = 10
    TIER_1_THRESHOLD = 50
    TIER_2_THRESHOLD = 100
    TIER_1_AUDIT = 10
    TIER_2_AUDIT = 15
    TIER_3_AUDIT = 20


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
    treatment = models.StringField(initial='')

    deposit_decision = models.CurrencyField(min=0, max=C.ENDOWMENT, label="Amount to deposit:")

    cash_kept = models.CurrencyField(initial=0)
    tax_paid_this_round = models.CurrencyField(initial=0)
    deposit_after_tax = models.CurrencyField(initial=0)

    deposit_before_spending = models.CurrencyField(initial=0)
    cash_before_spending = models.CurrencyField(initial=0)

    spend_from_cash = models.CurrencyField(min=0, initial=0, label="Amount to spend from cash:")
    spend_from_deposit = models.CurrencyField(min=0, initial=0, label="Amount to spend from deposit:")

    cash_verification_code = models.StringField(initial='')
    cash_verification_entry = models.StringField(
        blank=True, initial='',
        label="Type the code exactly as shown to confirm cash payment:"
    )

    total_deposit = models.CurrencyField(initial=0)
    total_cash = models.CurrencyField(initial=0)

    conversion_amount = models.CurrencyField(min=0, initial=0)
    cash_lost = models.CurrencyField(initial=0)
    conversion_untaxed = models.CurrencyField(initial=0)

    audit_probability = models.IntegerField(initial=0)
    random_draw = models.IntegerField(initial=0)
    was_audited = models.BooleanField(initial=False)
    fine_paid = models.CurrencyField(initial=0)
    tax_evaded_found = models.CurrencyField(initial=0)
    personal_audit_rate = models.IntegerField(initial=C.BASE_AUDIT_PROB)

    total_tax_paid = models.CurrencyField(initial=0)
    total_fines_paid = models.CurrencyField(initial=0)

    # Consent
    participant_full_name = models.StringField(label="Full name:")
    participant_email = models.StringField(label="Email address:")
    seat_number = models.IntegerField(label="Seat / PC number:", min=1, max=32)

    # Post-survey demographics
    age = models.IntegerField(label="Your age:", min=18, max=100)
    country_of_origin = models.StringField(label="Country of origin:")
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

    # Tax morale
    tax_morale = models.IntegerField(label="Cheating on taxes if you have a chance.", min=1, max=10)

    # Risk attitudes (4-domain, 0-10 sliders)
    risk_general  = models.IntegerField(label='How willing are you to take risks in general?', min=0, max=10)
    risk_financial = models.IntegerField(label='How willing are you to take risks in financial matters?', min=0, max=10)
    risk_career   = models.IntegerField(label='How willing are you to take risks in your occupation or career?', min=0, max=10)
    risk_health   = models.IntegerField(label='How willing are you to take risks regarding your health?', min=0, max=10)

    # Loss Aversion Scale
    loss_1 = models.IntegerField(label="When making a decision, I think much more about what might be lost than what might be gained.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_2 = models.IntegerField(label="The pain of losing money matters more than the pleasure of gaining the same amount of money.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_3 = models.IntegerField(label="I feel nervous when I have to make a decision that may lead to loss.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_4 = models.IntegerField(label="The pain from losing something matters much more to me than the pleasure from getting it.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_5 = models.IntegerField(label="Avoiding failure is less important to me than seeking success.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_6 = models.IntegerField(label="Experiencing a major loss stays in my mind longer than experiencing a major gain.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_7 = models.IntegerField(label="A potential failure scares me more than a potential success encourages me.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)
    loss_8 = models.IntegerField(label="The suffering that comes with losses can be fully offset by the pleasure that comes from gains.", choices=LIKERT_CHOICES, widget=widgets.RadioSelect)

    # HEXACO Honesty-Humility
    hh_1  = models.IntegerField(label="I wouldn't use flattery to get a raise or promotion at work.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_2  = models.IntegerField(label="I'm interested in making money primarily to have a luxurious lifestyle.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_3  = models.IntegerField(label="I wouldn't pretend to like someone just to get that person to do favors for me.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_4  = models.IntegerField(label="I'd get a lot of pleasure from owning expensive luxury goods.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_5  = models.IntegerField(label="I wouldn't feel bad about taking a bribe if it was very large.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_6  = models.IntegerField(label="I would be tempted to buy stolen property if I were financially tight.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_7  = models.IntegerField(label="I am an ordinary person who is no better than others.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_8  = models.IntegerField(label="I think that I am entitled to more respect than the average person is.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_9  = models.IntegerField(label="I wouldn't want people to treat me as though I were superior to them.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)
    hh_10 = models.IntegerField(label="I would like to know how to make lots of money in a dishonest manner.", choices=HEXACO_CHOICES, widget=widgets.RadioSelect)

    # Comprehension quiz
    quiz_q1 = models.StringField(blank=True, initial='', label="Your answer:")
    quiz_q2 = models.StringField(blank=True, initial='', label="Your answer:")
    quiz_q3 = models.StringField(blank=True, initial='', label="Your answer:")
    quiz_q1_first_correct = models.BooleanField(initial=False)
    quiz_q2_first_correct = models.BooleanField(initial=False)
    quiz_q3_first_correct = models.BooleanField(initial=False)

    @property
    def progress_pct(self):
        return int(self.round_number / C.NUM_ROUNDS * 100)

    def generate_verification_code(self):
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
        if self.treatment == 'baseline':
            return C.BASE_AUDIT_PROB
        if self.round_number < C.SHOCK_ROUND:
            return C.BASE_AUDIT_PROB
        elif self.round_number <= C.ELEVATED_AUDIT_END:
            return self.personal_audit_rate
        else:
            return C.BASE_AUDIT_PROB

    def carry_forward(self):
        if self.round_number > 1:
            prev = self.in_round(self.round_number - 1)
            self.total_deposit = prev.total_deposit
            self.total_cash = prev.total_cash
            self.personal_audit_rate = prev.personal_audit_rate
            self.total_tax_paid = prev.total_tax_paid
            self.total_fines_paid = prev.total_fines_paid
            if self.round_number <= C.ELEVATED_AUDIT_END:
                self.conversion_amount = prev.conversion_amount
                self.conversion_untaxed = prev.conversion_untaxed

        self.treatment = self.participant.vars.get('treatment', self.treatment or '')
        self.was_audited = False
        self.fine_paid = cu(0)
        self.tax_evaded_found = cu(0)
        self.random_draw = 0
        self.audit_probability = 0
        # Reset verification code each round so a fresh one is generated
        self.cash_verification_code = ''

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
            show_may_shock=(player.treatment in ['baseline', 'sudden']),
        )


class ShockPreAnnouncement(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 and player.treatment == 'preannounced'


class ComprehensionQuiz(Page):
    form_model = 'player'
    form_fields = [
        'quiz_q1', 'quiz_q2', 'quiz_q3',
        'quiz_q1_first_correct', 'quiz_q2_first_correct', 'quiz_q3_first_correct',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(correct_q1='70', correct_q2='45', correct_q3='5')


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
            return (
                f'The entered amount ({conversion} ECU) is greater than your cash in hand '
                f'({old_cash} ECU). Please enter an amount less than or equal to {old_cash} ECU.'
            )

    @staticmethod
    def vars_for_template(player: Player):
        prev = player.in_round(C.SHOCK_ROUND - 1)
        return dict(old_cash=prev.total_cash, progress_pct=player.progress_pct)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Save entered value BEFORE carry_forward overwrites conversion_amount with prev round's 0
        entered_conversion = player.conversion_amount or 0
        player.carry_forward()
        prev = player.in_round(C.SHOCK_ROUND - 1)
        old_cash = prev.total_cash
        converted = min(entered_conversion, old_cash)
        player.conversion_amount = converted
        player.conversion_untaxed = converted
        player.cash_lost = old_cash - converted
        player.total_deposit += converted
        player.total_cash = cu(0)
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
                if (
                    player.round_number <= C.ELEVATED_AUDIT_END
                    and player.treatment != 'baseline'
                    and player.round_number > C.SHOCK_ROUND
                ):
                    audit_prob = prev.personal_audit_rate
                else:
                    audit_prob = player.get_audit_probability()
            else:
                audit_prob = C.BASE_AUDIT_PROB
        # For rounds 8-10 in shock treatments, split deposit into safe vs untaxed converted
        in_elevated_window = (
            player.treatment != 'baseline'
            and C.SHOCK_ROUND <= player.round_number <= C.ELEVATED_AUDIT_END
        )
        if in_elevated_window:
            conversion_untaxed = player.conversion_untaxed or 0
            safe_deposit = current_deposit - conversion_untaxed
        else:
            conversion_untaxed = 0
            safe_deposit = current_deposit
        return dict(
            round_num=player.round_number,
            current_deposit=current_deposit,
            current_cash=current_cash,
            audit_prob=audit_prob,
            in_elevated_window=in_elevated_window,
            conversion_untaxed=conversion_untaxed,
            safe_deposit=safe_deposit,
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
        # FIX: Only generate a new code if one hasn't been set yet this round.
        # vars_for_template is called again on validation errors — regenerating
        # every call means the stored code never matches what the player typed.
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
        spend_deposit = values.get('spend_from_deposit') or 0
        if spend_cash < 0:
            return 'Cannot spend a negative amount from cash.'
        if spend_deposit < 0:
            return 'Cannot spend a negative amount from deposit.'
        total_spent = spend_cash + spend_deposit
        if total_spent != C.MANDATORY_SPENDING:
            return (
                f'The sum of cash and deposit spending must equal exactly {C.MANDATORY_SPENDING} ECU. '
                f'Currently you have {total_spent} ECU.'
            )
        if spend_cash > player.cash_before_spending:
            return (
                f'Not enough cash. You only have {player.cash_before_spending} ECU in cash '
                f'but are trying to spend {spend_cash} ECU.'
            )
        if spend_deposit > player.deposit_before_spending:
            return (
                f'Not enough in deposit. You only have {player.deposit_before_spending} ECU in deposit '
                f'but are trying to spend {spend_deposit} ECU.'
            )
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
        audited = player.random_draw <= (player.audit_probability or 0)
        in_elevated_window = (
            player.treatment != 'baseline'
            and C.SHOCK_ROUND <= player.round_number <= C.ELEVATED_AUDIT_END
        )
        converted_at_risk = player.conversion_untaxed if in_elevated_window else cu(0)
        auditable_base = player.total_cash + converted_at_risk
        if audited:
            evaded_tax     = auditable_base * C.TAX_RATE
            total_penalty  = evaded_tax + (evaded_tax * C.FINE_MULTIPLIER)
            cash_tax       = player.total_cash * C.TAX_RATE
            cash_fine      = cash_tax * C.FINE_MULTIPLIER
            converted_tax  = converted_at_risk * C.TAX_RATE
            converted_fine = converted_tax * C.FINE_MULTIPLIER
        else:
            evaded_tax = total_penalty = cash_tax = cash_fine = converted_tax = converted_fine = cu(0)
        return dict(
            was_audited=audited,
            random_draw=player.random_draw,
            audit_threshold=player.audit_probability,
            tax_evaded=evaded_tax,
            fine=total_penalty,
            cash_balance=player.total_cash,
            converted_at_risk=converted_at_risk,
            in_elevated_window=in_elevated_window,
            cash_tax=cash_tax,
            cash_fine=cash_fine,
            converted_tax=converted_tax,
            converted_fine=converted_fine,
            round_num=player.round_number,
            progress_pct=player.progress_pct,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        in_elevated_window = (
            player.treatment != 'baseline'
            and C.SHOCK_ROUND <= player.round_number <= C.ELEVATED_AUDIT_END
        )
        converted_at_risk = player.conversion_untaxed if in_elevated_window else cu(0)
        auditable_base = player.total_cash + converted_at_risk

        if player.random_draw <= (player.audit_probability or 0):
            player.was_audited = True
            evaded_tax    = auditable_base * C.TAX_RATE
            fine_only     = evaded_tax * C.FINE_MULTIPLIER
            total_penalty = evaded_tax + fine_only
            player.tax_evaded_found = evaded_tax
            player.fine_paid        = total_penalty
            player.total_fines_paid += total_penalty
            if player.total_deposit >= total_penalty:
                player.total_deposit -= total_penalty
            else:
                remaining = total_penalty - player.total_deposit
                player.total_deposit = cu(0)
                player.total_cash = max(cu(0), player.total_cash - remaining)
            if in_elevated_window:
                player.conversion_untaxed = cu(0)
            player.total_deposit += player.total_cash
            player.total_cash = cu(0)
        else:
            player.was_audited = False
            player.fine_paid = cu(0)
            player.tax_evaded_found = cu(0)


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
    form_fields = ['age', 'country_of_origin', 'gender']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class TaxMorale(Page):
    form_model = 'player'
    form_fields = ['tax_morale']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class RiskTaskEG(Page):
    form_model = 'player'
    form_fields = ['risk_general', 'risk_financial', 'risk_career', 'risk_health']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class LossAversion(Page):
    form_model = 'player'
    form_fields = ['loss_1', 'loss_2', 'loss_3', 'loss_4', 'loss_5', 'loss_6', 'loss_7', 'loss_8']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class RuleBreaking(Page):
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


class RegularisationNotice(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == C.ELEVATED_AUDIT_END + 1
            and player.treatment != 'baseline'
        )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            progress_pct=player.progress_pct,
            next_round=C.ELEVATED_AUDIT_END + 1,
        )


page_sequence = [
    Welcome,
    Instructions,
    ShockPreAnnouncement,
    ComprehensionQuiz,
    ShockAnnouncement,
    ConversionDecision,
    ConversionOutcome,
    RegularisationNotice,
    AllocationDecision,
    AllocationResult,
    SpendingDecision,
    AuditOutcome,
    RoundSummary,
    PostSurvey,
    TaxMorale,
    RiskTaskEG,
    LossAversion,
    RuleBreaking,
    FinalResults,
]