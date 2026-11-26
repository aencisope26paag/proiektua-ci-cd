"""Lector de datos del juego: .bin.json de un campeón (CommunityDragon) + plantillas de tooltip.

- Los VALORES (cifras, fórmulas, tabla de Shift) salen del .bin.json y son los del parche actual.
- Los TEXTOS salen de la plantilla de CommunityDragon en el idioma elegido; sus @Variables@ se
  resuelven con el .bin.json. Las etiquetas de Riot (<physicalDamage>, <status>...) se convierten en
  marcas {{t:clase}}...{{/t}} que el cliente pinta, así el coloreado no depende del idioma.
- Marcas propias que entiende el cliente:
    {{S|ad|bonus|60 / 67.5}}   escalado con una estadística (el cliente añade el % y la etiqueta)
    {{L|4|10}}                 valor que depende del nivel del campeón (1-18)
"""
import html
import re
from collections import ChainMap

# Deducido por votación sobre 60 campeones (probe_bin.py); ampliar cuando se confirmen más códigos.
STATS = {0: 'ap', 1: 'armor', 2: 'ad', 6: 'mr', 12: 'hp'}
SCOPES = {0: 'total', 1: 'base', 2: 'bonus'}
LEVELS = 18

TAG_CLASS = {
    'physicaldamage': 'phys', 'magicdamage': 'magic', 'truedamage': 'true', 'status': 'cc',
    'healing': 'heal', 'shield': 'shield', 'attackspeed': 'as', 'omnivamp': 'vamp', 'lifesteal': 'vamp',
    'scalead': 'ad', 'scalebonusad': 'ad', 'scaleap': 'ap', 'scalearmor': 'armor', 'scalemr': 'mr',
    'scalehealth': 'hp', 'scalemana': 'mana', 'speed': 'ms', 'onhit': 'onhit',
    'keywordmajor': 'kw', 'keywordstealth': 'kw', 'spellpassive': 'lbl', 'spellactive': 'lbl',
}
RULES_RE = re.compile(r'<rules[^>]*>(.*?)</rules>', re.S | re.I)
FLAVOR_RE = re.compile(r'<flavorText[^>]*>(.*?)</flavorText>', re.S | re.I)
TAG_RE = re.compile(r'<(/?)([A-Za-z][\w]*)[^>]*?(/?)>')
BR_RE = re.compile(r'<\s*(?:br\s*/?|/p|/li)\s*>', re.I)
VAR_RE = re.compile(r'@([^@\n]{1,80})@')


class Unsupported(Exception):
    pass


# ---------------------------------------------------------------- números
def num(x, decimals=None):
    x = round(float(x), 2 if decimals is None else decimals)
    if x == 0:
        x = 0.0
    s = f'{x:.{2 if decimals is None else decimals}f}'
    if decimals is None and '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def num_list(vals, decimals=None):
    shown = [num(v, decimals) for v in vals]
    return shown[0] if len(set(shown)) == 1 else ' / '.join(shown)


def ranks(vals, n):
    vals = list(vals)
    return vals[1:1 + n] if len(vals) > n else vals[:n]


# valores: ('c', [x]) constante | ('r', [..]) por rango | ('l', [..18]) por nivel
def _bin(a, b, op):
    (ka, va), (kb, vb) = a, b
    if ka == 'c' and kb == 'c':
        return ('c', [op(va[0], vb[0])])
    if ka == 'c':
        return (kb, [op(va[0], y) for y in vb])
    if kb == 'c':
        return (ka, [op(x, vb[0]) for x in va])
    if ka != kb or len(va) != len(vb):
        raise Unsupported('mixed')
    return (ka, [op(x, y) for x, y in zip(va, vb)])


def eval_part(p, ctx):
    t = p.get('__type')
    dv, n = ctx['dv'], ctx['n']
    if t == 'EffectValueCalculationPart':
        return ('r', ranks(ctx['effects'][int(p.get('mEffectIndex', 1)) - 1], n))
    if t == 'NumberCalculationPart':
        return ('c', [p.get('mNumber', 0.0)])
    if t == 'NamedDataValueCalculationPart':
        name = p['mDataValue'].lower()
        if name in dv:
            return ('r', ranks(dv[name], n))
        base, _stats = eval_calc(ctx['calcs'][name], ctx)      # referencia a otro cálculo
        if base is None:
            raise Unsupported('cálculo sin parte numérica')
        return base
    if t == 'ByCharLevelInterpolationCalculationPart':
        a, b = p['mStartValue'], p['mEndValue']
        return ('l', [a + (b - a) * (lv - 1) / (LEVELS - 1) for lv in range(1, LEVELS + 1)])
    if t == 'ByCharLevelBreakpointsCalculationPart':
        bps = p.get('mBreakpoints') or []
        return ('l', [p.get('mLevel1Value', 0.0) + sum(b.get('mAdditionalBonusAtThisLevel', 0.0)
                                                         for b in bps if b.get('mLevel', 99) <= lv)
                      for lv in range(1, LEVELS + 1)])
    if t == 'SumOfSubPartsCalculationPart':
        acc = ('c', [0.0])
        for sp in p.get('mSubparts') or []:
            acc = _bin(acc, eval_part(sp, ctx), lambda x, y: x + y)
        return acc
    if t == 'ProductOfSubPartsCalculationPart':
        return _bin(eval_part(p['mPart1'], ctx), eval_part(p['mPart2'], ctx), lambda x, y: x * y)
    raise Unsupported(t)


def eval_calc(calc, ctx):
    if calc.get('__type') == 'GameCalculationModified':
        base, stats = eval_calc(ctx['calcs'][calc['mModifiedGameCalculation'].lower()], ctx)
        mult = eval_part(calc['mMultiplier'], ctx)
        mul = lambda x, y: x * y
        return (_bin(base, mult, mul) if base else None,
                [dict(s, val=_bin(s['val'], mult, mul)) for s in stats])
    if calc.get('__type') == 'GameCalculationConditional':
        default = calc.get('mDefaultGameCalculation')
        if isinstance(default, str) and default.lower() in ctx['calcs']:
            return eval_calc(ctx['calcs'][default.lower()], ctx)
        raise Unsupported('GameCalculationConditional sin cálculo por defecto')
    if calc.get('__type') != 'GameCalculation':
        raise Unsupported(calc.get('__type'))
    base, stats = None, []
    for p in calc.get('mFormulaParts') or []:
        t = p.get('__type')
        if t in ('StatByNamedDataValueCalculationPart', 'StatByCoefficientCalculationPart',
                 'StatBySubPartCalculationPart'):
            if t == 'StatByNamedDataValueCalculationPart':
                val = ('r', ranks(ctx['dv'][p['mDataValue'].lower()], ctx['n']))
            elif t == 'StatByCoefficientCalculationPart':
                val = ('c', [p.get('mCoefficient', 0.0)])
            else:
                val = eval_part(p['mSubpart'], ctx)
            code = p.get('mStat', 0)
            stats.append({'stat': STATS.get(code, f'stat{code}'),
                          'scope': SCOPES.get(p.get('mStatFormula', 0), 'total'), 'val': val})
        else:
            v = eval_part(p, ctx)
            base = v if base is None else _bin(base, v, lambda x, y: x + y)
    if calc.get('mMultiplier'):          # p. ej. 0.01 en la E de Aatrox (valores guardados como porcentaje)
        mult = eval_part(calc['mMultiplier'], ctx)
        mul = lambda x, y: x * y
        base = _bin(base, mult, mul) if base else None
        stats = [dict(s, val=_bin(s['val'], mult, mul)) for s in stats]
    return base, stats


# ---------------------------------------------------------------- variables @...@
PER_100_STATS = ('hp', 'armor', 'mr', 'mana', 'ap', 'ad')


def stat_display(stat, vals):
    """Coeficiente (fracción) -> (valores en %, ¿'por cada 100'?). Un coeficiente por punto de vida tan
    pequeño (<0.5%) solo tiene sentido como "X% por cada 100 de vida", que es como lo muestra el juego."""
    pct = [v * 100 for v in vals]
    if stat in PER_100_STATS and pct and all(0 < abs(x) < 0.5 for x in pct):
        return [x * 100 for x in pct], True
    return pct, False


def render_var(expr, ctx):
    if expr.startswith('SpellModifier'):
        return ''
    raw_expr = expr
    mult, decimals = 1.0, None
    m = re.match(r'^(.*?)\s*\*\s*(-?[\d.]+)$', expr.strip())
    if m:
        expr, mult = m.group(1), float(m.group(2))
    m = re.match(r'^(.*)\.(\d)$', expr)
    if m:
        expr, decimals = m.group(1), int(m.group(2))
    name = expr.split(':')[-1].strip().lower()
    reason = 'no existe en el .bin'
    try:
        me = re.match(r'^effect(\d+)amount$', name)
        if name not in ctx['dv'] and name not in ctx['calcs']:
            builtin = (ctx['effects'][int(me.group(1)) - 1] if me else
                       ctx['cooldown'] if name == 'cooldown' else
                       ctx['mana'] if name in ('cost', 'abilityresourcecost') else None)
            if builtin:
                return num_list([v * mult for v in ranks(builtin, ctx['n'])], decimals)
        if name in ctx['dv']:
            return num_list([v * mult for v in ranks(ctx['dv'][name], ctx['n'])], decimals)
        if name in ctx['calcs']:
            base, stats = eval_calc(ctx['calcs'][name], ctx)
            out = []
            if base:
                kind, vals = base
                vals = [v * mult for v in vals]
                out.append('{{L|%s|%s}}' % (num(vals[0], decimals), num(vals[-1], decimals)) if kind == 'l'
                           else num_list(vals, decimals))
            for s in stats:
                kind, vals = s['val']
                vals, per = stat_display(s['stat'], vals)
                text = (f'{num(vals[0])}–{num(vals[-1])}' if kind == 'l' else num_list(vals))
                out.append('{{S|%s|%s|%s%s}}' % (s['stat'], s['scope'], text, '|100' if per else ''))
            if out:
                return out[0] + ''.join(f' (+ {o})' for o in out[1:])
            reason = 'cálculo vacío'
    except (Unsupported, KeyError, IndexError, TypeError) as e:
        reason = f'{type(e).__name__}: {e}'
    ctx.setdefault('unresolved', []).append(f'{raw_expr} ({reason})')
    return '?'


def render_template(raw, ctx):
    """Texto de Riot -> texto con marcas {{...}} y variables resueltas."""
    raw = BR_RE.sub('\n', raw or '')
    raw = VAR_RE.sub(lambda m: render_var(m.group(1), ctx), raw)
    stack = []

    def tag(m):
        closing, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if selfclose:
            return ''
        if closing:
            return '{{/t}}' if stack and stack.pop() else ''
        cls = TAG_CLASS.get(name)
        stack.append(bool(cls))
        return '{{t:%s}}' % cls if cls else ''

    text = TAG_RE.sub(tag, raw)
    text = html.unescape(text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return re.sub(r'\s*\n\s*', '\n', text).strip()


def split_template(raw, ctx):
    """(texto principal, [notas <rules>], ambientación <flavorText>)"""
    raw = raw or ''
    rules = [render_template(r, ctx) for r in RULES_RE.findall(raw)]
    flavor = ' '.join(render_template(f, ctx) for f in FLAVOR_RE.findall(raw))
    main = FLAVOR_RE.sub('', RULES_RE.sub('', raw))
    return render_template(main, ctx), [r for r in rules if r], flavor.strip()


# ---------------------------------------------------------------- fichero .bin.json
def parse_bin(doc):
    """{'P': ctx, 'Q': ctx, ...} con DataValues, cálculos, enfriamiento, coste y filas de la tabla."""
    root_key = next(k for k in doc if k.endswith('/CharacterRecords/Root'))
    prefix = root_key.split('/CharacterRecords')[0]
    root = doc[root_key]

    all_dv, all_calcs = {}, {}
    for obj in doc.values():
        sp_ = obj.get('mSpell') if isinstance(obj, dict) else None
        if isinstance(sp_, dict):
            for x in sp_.get('DataValues') or []:
                all_dv.setdefault(x['name'].lower(), x['values'])
            for k, v in (sp_.get('mSpellCalculations') or {}).items():
                all_calcs.setdefault(k.lower(), v)

    def load(path):
        obj = doc.get(path) or doc.get(f'{prefix}/Spells/{path}')
        sp = (obj or {}).get('mSpell')
        if not sp:
            return None
        td = (sp.get('mClientData') or {}).get('mTooltipData') or {}
        level_up = ((td.get('mLists') or {}).get('LevelUp')) or {}
        own_dv = {x['name'].lower(): x['values'] for x in sp.get('DataValues') or []}
        own_calcs = {k.lower(): v for k, v in (sp.get('mSpellCalculations') or {}).items()}
        calc_names = {k.lower(): k for k in (sp.get('mSpellCalculations') or {})}
        return {
            'dv': ChainMap(own_dv, all_dv), 'calcs': ChainMap(own_calcs, all_calcs),
            'own_calcs': own_calcs, 'calc_names': calc_names,
            'cooldown': sp.get('cooldownTime'), 'mana': sp.get('mana'),
            'effects': [e.get('value') or [] for e in sp.get('mEffectAmount') or [] if isinstance(e, dict)],
            'rows': level_up.get('Elements') or [], 'n': level_up.get('levelCount') or 5,
        }

    slots = {}
    for key, name in zip('QWER', root.get('spellNames') or []):
        ctx = load(name)
        if ctx:
            slots[key] = ctx
    if root.get('mCharacterPassiveSpell'):
        ctx = load(root['mCharacterPassiveSpell'])
        if ctx:
            slots['P'] = ctx
    slots['_resource'] = (root.get('primaryAbilityResource') or {}).get('arType')
    return slots


# ---------------------------------------------------------------- tabla de Shift -> "leveling"
SCALAR_RE = re.compile(r'^(Total|Bonus|Base)?(AD|AP|Armor|MR|MagicResist(?:ance)?|MaxHealth|BonusHealth|Health|Mana)'
                       r'(?:Scalar|Ratio|Scaling)$', re.I)
STAT_WORD = {'ad': 'AD', 'ap': 'AP', 'armor': 'armor', 'mr': 'magic resistance', 'magicresist': 'magic resistance',
             'magicresistance': 'magic resistance', 'health': 'health', 'maxhealth': 'max health',
             'bonushealth': 'bonus health', 'mana': 'mana'}


def row_key(name_override):
    return re.sub(r'^Spell_(?:ListType|[A-Za-z0-9]+)_', '', name_override or '')


def row_label(name_override):
    return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', row_key(name_override)).strip()


UNIT_STAT = {'ad': 'AD', 'ap': 'AP', 'armor': 'armor', 'mr': 'magic resistance', 'hp': 'health'}
DAMAGE_WORD = {'PHYSICAL_DAMAGE': 'Physical Damage', 'MAGIC_DAMAGE': 'Magic Damage', 'TRUE_DAMAGE': 'True Damage'}


def humanize(s):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', s).strip()


def calc_label(name, dmg):
    """QEdgeDamage / Calc_Minion_Execute_Amp -> 'Edge Physical Damage' / 'Minion Execute Amp'.
    Se quita la letra de la tecla, 'Calc' y 'Total'; 'Damage' toma el tipo de daño de la habilidad
    salvo que el nombre ya lo indique ('Magic Damage Reduction' se deja tal cual)."""
    s = re.sub(r'^Calc[_ ]', '', name).replace('_', ' ')
    words = [w for w in humanize(s).split() if w not in ('Total', 'Calc')]
    if words and words[0] in ('P', 'Q', 'W', 'E', 'R'):
        words = words[1:]
    label = ' '.join(words) or 'Value'
    if dmg in DAMAGE_WORD and not re.search(r'\b(Physical|Magic|True|Reduction|Resist\w*)\b', label):
        label = re.sub(r'\bDamage\b', DAMAGE_WORD[dmg], label)
    return label


PERCENT_WORDS = re.compile(r'(Reduction|Percent|Amp|Chance|Threshold|Ratio|Resist)', re.I)


def pct_used(raw):
    """Nombres de cálculo que la propia plantilla multiplica por 100 (=> son porcentajes)."""
    out = set()
    for m in VAR_RE.finditer(raw or ''):
        mm = re.match(r'^(.*?)\s*\*\s*100(?:\.0+)?$', m.group(1).strip())
        if mm:
            out.add(re.sub(r'\.\d$', '', mm.group(1)).split(':')[-1].strip().lower())
    return out


def used_names(calc, ctx, seen=None):
    """Nombres de DataValues usados por un cálculo (para saber qué filas de la tabla ya cubre)."""
    seen = seen if seen is not None else set()
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('mDataValue'), str):
                seen.add(o['mDataValue'].lower())
            ref = o.get('mModifiedGameCalculation')
            if isinstance(ref, str) and ref.lower() in ctx['calcs']:
                walk(ctx['calcs'][ref.lower()])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(calc)
    return seen


def calc_rows(ctx, dmg):
    """Una línea por cada cálculo de la habilidad: 'Edge Physical Damage: 17.5 / 43.75 (+ 105% AD)'."""
    rows, covered = [], set()
    for cname, calc in ctx['own_calcs'].items():
        if cname.endswith('cooldown') or 'cost' in cname or cname.startswith('{'):
            continue   # los nombres entre llaves son hashes sin nombre conocido (duplican otras líneas)
        try:
            base, stats = eval_calc(calc, ctx)
        except (Unsupported, KeyError, IndexError, TypeError):
            continue
        if base is None and not stats:
            continue
        label = calc_label(ctx['calc_names'][cname], dmg)
        pct = bool(calc.get('mDisplayAsPercent')) or cname in ctx.get('pct_used', ())
        if not pct and base and base[0] != 'c' and all(0 < abs(v) <= 1.0 for v in base[1]) and PERCENT_WORDS.search(label):
            pct = True      # fracciones con nombre de porcentaje (p. ej. 'Physical Damage Reduction': 0.125)
        mods = []
        if base:
            mods.append({'values': [round(v * (100 if pct else 1), 4) for v in base[1]], 'units': ['%' if pct else '']})
        for s in stats:
            scope = '' if s['scope'] == 'total' else f"{s['scope']} "
            vals, per = stat_display(s['stat'], s['val'][1])
            mods.append({'values': [round(v, 4) for v in vals],
                         'units': [f"%{' per 100' if per else ''} {scope}{UNIT_STAT.get(s['stat'], s['stat'])}"]})
        rows.append({'attribute': label, 'modifiers': mods})
        used_names(calc, ctx, covered)
    return rows, covered


def build_leveling(ctx, dmg=None):
    rows, covered = calc_rows(ctx, dmg)
    return rows + table_rows(ctx, covered)


def table_rows(ctx, covered):
    """Filas de la tabla de Shift del juego que ningún cálculo cubre (ralentización, curación aumentada...)."""
    out, last_base = [], None
    for e in ctx['rows']:
        t = (e.get('type') or '')
        tl = t.lower()
        if tl in covered:
            continue
        if tl == 'cooldown' or tl.startswith('cost') or tl.startswith('mana'):
            continue
        mult = e.get('multiplier', 1.0)
        if tl in ctx['dv']:
            vals = ranks(ctx['dv'][tl], ctx['n'])
        elif tl in ctx['calcs']:
            try:
                base, _ = eval_calc(ctx['calcs'][tl], ctx)
            except (Unsupported, KeyError):
                continue
            if not base or base[0] != 'r':
                continue
            vals = base[1]
        else:
            continue
        vals = [round(v * mult, 4) for v in vals]
        key = row_key(e.get('nameOverride'))
        sm = SCALAR_RE.match(key)
        if sm:
            scope = (sm.group(1) or '').lower()
            stat = STAT_WORD[sm.group(2).lower()]
            unit = '%' + (f' {scope}' if scope not in ('', 'total') else '') + f' {stat}'
            if last_base is not None:
                last_base['modifiers'].append({'values': vals, 'units': [unit]})
                continue
            out.append({'attribute': row_label(e.get('nameOverride')), 'modifiers': [{'values': vals, 'units': [unit]}]})
            continue
        item = {'attribute': row_label(e.get('nameOverride')) or t,
                'modifiers': [{'values': vals, 'units': ['%' if abs(mult) == 100 else '']}]}
        out.append(item)
        last_base = item
    return out


# ---------------------------------------------------------------- campeón completo
def damage_type(raw):
    low = (raw or '').lower()
    for tag, kind in (('<physicaldamage', 'PHYSICAL_DAMAGE'), ('<magicdamage', 'MAGIC_DAMAGE'),
                      ('<truedamage', 'TRUE_DAMAGE')):
        if tag in low:
            return kind
    return None


RESOURCE_NAMES = {0: 'Mana', 1: 'Energy'}


def build_champion(bin_doc, cd, icon_url):
    slots = parse_bin(bin_doc)
    resource = RESOURCE_NAMES.get(slots.pop('_resource', None))

    def spell_from(ctx, name, icon, raw):
        ctx['pct_used'] = pct_used(raw)
        main, rules, flavor = split_template(raw, ctx)
        dmg = damage_type(raw)
        spell = {'name': name, 'icon': icon, 'rich': True, 'richNotes': True, 'damageType': dmg,
                 'effects': [{'description': main, 'leveling': build_leveling(ctx, dmg)}],
                 'ttNotes': rules, 'ttFlavor': flavor, 'cooldown': None, 'cost': None}
        cdv = [v for v in ranks(ctx['cooldown'], ctx['n'])] if ctx['cooldown'] else None
        if not cdv:   # pasivas: cálculo "...Cooldown" dependiente del nivel
            for cname, calc in ctx['calcs'].items():
                if cname.endswith('cooldown'):
                    try:
                        base, _ = eval_calc(calc, ctx)
                        cdv = [round(v, 2) for v in base[1]] if base else None
                    except (Unsupported, KeyError):
                        pass
                    break
        if cdv:
            spell['cooldown'] = {'modifiers': [{'values': cdv, 'units': ['']}]}
        if ctx['mana']:
            spell['cost'] = {'modifiers': [{'values': ranks(ctx['mana'], ctx['n']), 'units': ['']}]}
            if resource:
                spell['costType'] = resource
        return spell

    p = cd.get('passive') or {}
    abilities = {}
    if 'P' in slots:
        abilities['P'] = [spell_from(slots['P'], p.get('name', ''), icon_url(p.get('abilityIconPath')),
                                     p.get('dynamicDescription') or p.get('description', ''))]
    for sp in cd.get('spells', []):
        key = sp['spellKey'].upper()
        if key not in slots:
            continue
        spell = spell_from(slots[key], sp.get('name', ''), icon_url(sp.get('abilityIconPath')),
                           sp.get('dynamicDescription') or sp.get('description', ''))
        ammo = (sp.get('ammo') or {}).get('maxAmmo') if isinstance(sp.get('ammo'), dict) else None
        if isinstance(ammo, (int, float)) and ammo > 1:
            spell['charges'] = ammo
        abilities[key] = [spell]
    if len(abilities) < 2:
        raise Unsupported('sin habilidades en el .bin')
    gaps = {k: slots[k]['unresolved'] for k in abilities if slots[k].get('unresolved')}
    return {'name': cd.get('name', ''), 'title': cd.get('title', ''), 'abilities': abilities,
            '_source': 'gamedata', '_unresolved': gaps}
