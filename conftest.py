"""Datos de ejemplo inventados (no son datos de Riot) con la misma estructura que los .bin.json reales."""
import pytest

import server


def dv(name, values):
    return {'name': name, 'values': values}


def calc(parts, **extra):
    return {'__type': 'GameCalculation', 'mFormulaParts': parts, **extra}


def named(name):
    return {'__type': 'NamedDataValueCalculationPart', 'mDataValue': name}


def stat_by_dv(name, stat, formula=0):
    part = {'__type': 'StatByNamedDataValueCalculationPart', 'mDataValue': name, 'mStat': stat}
    if formula:
        part['mStatFormula'] = formula
    return part


def number(x):
    return {'__type': 'NumberCalculationPart', 'mNumber': x}


def spell(values, calcs=None, cooldown=None, mana=None, rows=None, levels=5):
    return {'__type': 'SpellObject', 'mSpell': {
        'DataValues': [dv(k, v) for k, v in values.items()],
        'mSpellCalculations': calcs or {},
        'cooldownTime': cooldown, 'mana': mana,
        'mClientData': {'mTooltipData': {'mLists': {'LevelUp': {'levelCount': levels, 'Elements': rows or []}}}},
    }}


@pytest.fixture
def mini_bin():
    """Campeón ficticio: Q con escalado de AD, ralentización y daño derivado; W con escudo; pasiva por nivel."""
    q = spell(
        {'QBaseDamage': [0, 10, 20, 30, 40, 50, 60], 'QADRatio': [0, .5, .6, .7, .8, .9, 1.0],
         'QSlow': [0, -.2, -.25, -.3, -.35, -.4, -.45]},
        calcs={
            'QDamage': calc([named('QBaseDamage'), stat_by_dv('QADRatio', 2, formula=2)]),
            'QEdgeDamage': {'__type': 'GameCalculationModified', 'mModifiedGameCalculation': 'QDamage',
                            'mMultiplier': number(1.5)},
            '{deadbeef}': calc([named('QBaseDamage')]),          # nombre-hash: debe omitirse
        },
        cooldown=[0, 10, 9, 8, 7, 6, 6], mana=[0, 50, 55, 60, 65, 70, 70],
        rows=[{'type': 'Cooldown'}, {'type': 'QSlow', 'nameOverride': 'Spell_ListType_Slow', 'multiplier': -100.0}])
    w = spell({'WShield': [0, 40, 60, 80, 100, 120, 120]}, cooldown=[0, 20, 19, 18, 17, 16, 16],
              rows=[{'type': 'WShield', 'nameOverride': 'Spell_ListType_ShieldStrength', 'multiplier': 1.0}])
    p = spell({}, calcs={
        'PDamage': calc([{'__type': 'ByCharLevelInterpolationCalculationPart', 'mStartValue': .04, 'mEndValue': .10}],
                        mDisplayAsPercent=True),
        'PCooldown': calc([{'__type': 'ByCharLevelInterpolationCalculationPart', 'mStartValue': 22, 'mEndValue': 10}]),
    })
    return {
        'Characters/Mini/CharacterRecords/Root': {
            'spellNames': ['MiniQ', 'MiniW'], 'mCharacterPassiveSpell': 'Characters/Mini/Spells/MiniP',
            'primaryAbilityResource': {'arType': 0}},
        'Characters/Mini/Spells/MiniQ': q,
        'Characters/Mini/Spells/MiniW': w,
        'Characters/Mini/Spells/MiniP': p,
    }


@pytest.fixture
def mini_cd():
    icon = '/lol-game-data/assets/ASSETS/Characters/Mini/Icons/{}.png'
    return {
        'name': 'Mini', 'title': 'The Test Dummy',
        'passive': {'name': 'Dummy Passive', 'abilityIconPath': icon.format('P'),
                    'description': 'Attacks deal <magicDamage>@PDamage*100@% max Health</magicDamage>.'},
        'spells': [
            {'spellKey': 'q', 'name': 'Quick Strike', 'maxLevel': 5, 'abilityIconPath': icon.format('Q'),
             'dynamicDescription': 'Deals <physicalDamage>@QDamage@ physical damage</physicalDamage> and '
                                   '<status>Slows</status> by @QSlow*-100@%. Edge hits for @QEdgeDamage@.'
                                   '<br><br><rules>Range grows with size.</rules>'
                                   '<flavorText>"Hello."</flavorText>'},
            {'spellKey': 'w', 'name': 'Wall', 'maxLevel': 5, 'abilityIconPath': icon.format('W'),
             'dynamicDescription': 'Shields for <shield>@WShield@</shield>. Unknown: @Nope@.'},
        ],
    }


@pytest.fixture(autouse=True)
def clean_cache():
    """La caché del servidor es global: se vacía antes y después de cada test."""
    server._cache.clear()
    yield
    server._cache.clear()
