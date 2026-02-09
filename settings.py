from os import environ

SESSION_CONFIGS = [
    dict(
        name='demonetisation_sudden',
        display_name='Demonetisation - Sudden Shock',
        app_sequence=['demonetisation_experiment'],
        num_demo_participants=1,
        treatment='sudden',
        real_world_currency_per_point=0.01,
        consent_link='https://your-qualtrics-link.com',
    ),
    dict(
        name='demonetisation_preannounced',
        display_name='Demonetisation - Pre-announced Shock',
        app_sequence=['demonetisation_experiment'],
        num_demo_participants=1,
        treatment='preannounced',
        real_world_currency_per_point=0.01,
        consent_link='https://your-qualtrics-link.com',
    ),
    dict(
        name='demonetisation_baseline',
        display_name='Demonetisation - Baseline (Control)',
        app_sequence=['demonetisation_experiment'],
        num_demo_participants=1,
        treatment='baseline',
        real_world_currency_per_point=0.01,
        consent_link='https://your-qualtrics-link.com',
    ),
]

# Default session settings
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.01,
    participation_fee=0.00,
    doc="Demonetisation experiment on tax compliance and liquidity shock",
)

PARTICIPANT_FIELDS = ['treatment']
SESSION_FIELDS = []

# ISO-639 language code
LANGUAGE_CODE = 'en'

# Currency settings
REAL_WORLD_CURRENCY_CODE = 'GBP'
USE_POINTS = True
POINTS_CUSTOM_NAME = 'ECU'

# Admin settings
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

# Demo page intro
DEMO_PAGE_INTRO_HTML = """
Demonetisation Experiment:
Tax Compliance and Liquidity Shock
"""

# Secret key (leave as any random string for local use)
SECRET_KEY = 'change-this-to-any-random-string-for-production'

# IMPORTANT: Do NOT set INSTALLED_APPS manually in oTree 6
