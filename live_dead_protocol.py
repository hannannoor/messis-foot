"""Live/dead sequence experiment: fixed identities, cases, timing and the frozen release model.

The budget clock started at the first implementation action after plan approval (Asia/Singapore).
"""
from datetime import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENT = 'live-dead-sequence-2026-11-14'
START_LOCAL = '2026-11-14T15:03:04+08:00'
DEADLINE_LOCAL = '2026-11-15T15:03:04+08:00'
SEED_PREFIX = 'live-dead-sequence-v1:1729:'

SKILLCORNER = ('1874553', '1886347', '2007448', '2007721', '2010085', '2011166', '2013725', '2015213', '2016236',
               '2017461')
PRIMARY = tuple('skillcorner-' + m for m in SKILLCORNER) + ('dfl-J03WR9', 'dfl-J03WN1', 'wcsf-used-match')
SECONDARY = ('dfl-J03WOH', 'dfl-J03WOY')
CASES = PRIMARY + SECONDARY
TRAIN_MATCHES = ('J03WOH', 'J03WOY', 'J03WPY', 'J03WMX')
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')
# Experiment E's committed control refit, which reproduces the frozen release model digest exactly.
FROZEN_MODEL_PATH = ROOT / 'reports/player-stillness/2026-11-12-a/models/control.json'


def provider_of(cid):
    provider = cid.split('-', 1)[0]
    if provider not in PROVIDERS:
        raise ValueError('Unknown provider')
    return provider


def enforce_deadline(at=None):
    from datetime import timezone
    now = datetime.now(timezone.utc) if at is None else at
    if now.tzinfo is None:
        raise ValueError('Timezone-aware time required')
    if now > datetime.fromisoformat(DEADLINE_LOCAL):
        raise ValueError('Budget deadline passed: ' + DEADLINE_LOCAL)


def load_frozen_model():
    from memory_ablation import MODEL_SHA
    from memory_ablation_training import model_digest
    model = json.loads(FROZEN_MODEL_PATH.read_text(encoding='utf-8'))['model']
    if model_digest(model) != MODEL_SHA:
        raise ValueError('Frozen model artifact differs from the release model digest')
    return model
