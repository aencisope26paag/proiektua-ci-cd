#!/usr/bin/env python3
"""Servidor local para LoL Tooltip Inspector (http://localhost:8000).

Endpoints:
  /api/list?lang=es|en       lista de campeones (CommunityDragon)
  /api/version               parche actual
  /api/icons                 iconos disponibles en ./icons
  /api/champion/<alias>_<id> habilidades (Meraki + notas de CommunityDragon; respaldo CD)
  /api/debug/<id>            textos crudos de CommunityDragon (diagnóstico)
"""
import html
import http.server
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
ICONS_DIR = BASE_DIR / 'icons'
HOST, PORT = 'localhost', 8000
CACHE_TTL = 3600  # segundos

CD = 'https://raw.communitydragon.org/latest'
GAME_DATA = f'{CD}/plugins/rcp-be-lol-game-data/global'
MERAKI = 'https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/champions'
HEADERS = {'User-Agent': 'lol-tooltip-inspector/2.0'}

# Verificación TLS activada por defecto. Si tu red lo impide: LOL_INSECURE=1
SSL_CTX = (ssl._create_unverified_context() if os.environ.get('LOL_INSECURE') == '1'
           else ssl.create_default_context())

_cache = {}
_cache_lock = threading.Lock()


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return json.loads(resp.read())


def cached(key, loader, ttl=CACHE_TTL):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    value = loader()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def public_patch(version):
    """Versión interna de Riot (16.22.x) -> pública (26.22)."""
    parts = version.split('.')
    major = int(parts[0])
    if major >= 14:
        major += 10
    return f'{major}.{parts[1]}'


# ---------------------------------------------------------------- lista / versión
def get_version():
    cd_ver = fetch_json(f'{CD}/content-metadata.json').get('version', '')
    return {'patch': public_patch(cd_ver), 'full': cd_ver}


# Carpetas de idioma de CommunityDragon (el inglés vive en 'default')
LOCALE_FOLDERS = {'en': ('default', 'en_gb'), 'es': ('es_es',)}


def fetch_locale(path, lang):
    last = None
    for loc in LOCALE_FOLDERS[lang]:
        try:
            return fetch_json(f'{GAME_DATA}/{loc}/v1/{path}')
        except Exception as e:
            last = e
    raise last


def get_champion_list(lang='en'):
    raw = fetch_locale('champion-summary.json', lang)
    champs = {}
    for c in raw:
        if 0 < c['id'] < 1000:
            champs[c['alias']] = {
                'id': c['alias'],
                'numId': c['id'],
                'name': c['name'],
                'icon': f"{GAME_DATA}/default/v1/champion-icons/{c['id']}.png",
            }
    return {'data': champs}


# ---------------------------------------------------------------- respaldo CommunityDragon
TAG_BREAK_RE = re.compile(r'<\s*(?:br\s*/?|/p|/li)\s*>', re.I)
TAG_RE = re.compile(r'<[^>]+>')
VAR_RE = re.compile(r'@([^@\n]{1,80})@')
EXPR_RE = re.compile(r'^\s*([\w.:]+)\s*(?:([*/])\s*(-?[\d.]+))?\s*$')


def fmt_num(x):
    x = round(float(x), 2)
    return str(int(x)) if x == int(x) else str(x)


def icon_url(path):
    return (path or '').lower().replace('/lol-game-data/assets/', f'{GAME_DATA}/default/')


def rank_values(arr, max_level):
    """Quita el hueco del índice 0 y recorta a los rangos reales de la habilidad."""
    arr = list(arr)
    if len(arr) > max_level and arr and arr[0] == 0:
        arr = arr[1:]
    return arr[:max_level]


def build_vars(spell, max_level):
    out = {}
    for src in (spell.get('effectAmounts'), spell.get('coefficients')):
        for k, v in (src or {}).items():
            out[k.lower()] = v
    for k, v in out.items():
        if isinstance(v, list):
            out[k] = rank_values(v, max_level)
    return out


def resolve_expr(expr, variables):
    m = EXPR_RE.match(expr)
    if not m:
        return None
    name = m.group(1).split(':')[-1].split('.')[-1].lower()
    val = variables.get(name)
    if val is None:
        return None
    vals = val if isinstance(val, list) else [val]
    try:
        nums = [float(v) for v in vals]
    except (TypeError, ValueError):
        return None
    if m.group(2):
        k = float(m.group(3))
        nums = [n * k if m.group(2) == '*' else (n / k if k else n) for n in nums]
    if not any(nums):           # todo ceros: CommunityDragon no trae el valor real
        return None
    uniq = []
    for n in nums:
        s = fmt_num(n)
        if s not in uniq:
            uniq.append(s)
    return ' / '.join(uniq) if len(uniq) > 1 else (uniq[0] if uniq else None)


RULES_RE = re.compile(r'<rules[^>]*>(.*?)</rules>', re.S | re.I)
FLAVOR_RE = re.compile(r'<flavorText[^>]*>(.*?)</flavorText>', re.S | re.I)


def split_description(raw, variables):
    """Separa el texto principal de las notas (<rules>) y la ambientación (<flavorText>)."""
    raw = raw or ''
    rules = [clean_description(r, variables) for r in RULES_RE.findall(raw)]
    flavor = [clean_description(f, variables) for f in FLAVOR_RE.findall(raw)]
    main = FLAVOR_RE.sub('', RULES_RE.sub('', raw))
    return clean_description(main, variables), [r for r in rules if r], ' '.join(f for f in flavor if f)


def clean_description(text, variables):
    if not text:
        return ''
    text = TAG_BREAK_RE.sub('\n', text)
    text = VAR_RE.sub(lambda m: '' if m.group(1).startswith('SpellModifier')
                      else (resolve_expr(m.group(1), variables) or '?'), text)
    text = TAG_RE.sub('', text)
    text = html.unescape(text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\s*\n\s*', '\n', text).strip()
    return text


def cd_spell_texts(cd):
    """{'P': (texto, notas, ambientación), 'Q': ...} a partir del JSON de CommunityDragon."""
    p = cd.get('passive') or {}
    out = {'P': split_description(p.get('description', ''), {})}
    for sp in cd.get('spells', []):
        max_level = int(sp.get('maxLevel') or 5)
        raw = sp.get('dynamicDescription') or sp.get('description', '')
        out[sp['spellKey'].upper()] = split_description(raw, build_vars(sp, max_level))
    return out


NUM_RE = re.compile(r'\d+(?:\.\d+)?')


def flat_numbers(seq):
    """Aplana listas anidadas y extrae números también de textos ("9 / 8.5"); ignora el resto."""
    if seq is None:
        return []
    if isinstance(seq, str):
        return [float(n) for n in NUM_RE.findall(seq)]
    if isinstance(seq, bool):
        return []
    if isinstance(seq, (int, float)):
        return [seq]
    out = []
    for x in seq if isinstance(seq, (list, tuple)) else []:
        out.extend(flat_numbers(x))
    return out


def adapt_cdragon(cd, num_id):
    def numeric(seq, max_level):
        return [x for x in rank_values(flat_numbers(seq), max_level) if x > 0]

    texts = cd_spell_texts(cd)
    p = cd.get('passive') or {}
    main, rules, flavor = texts['P']
    abilities = {'P': [{
        'name': p.get('name', 'Passive'),
        'icon': icon_url(p.get('abilityIconPath')),
        'effects': [{'description': main, 'leveling': []}],
        'ttNotes': rules, 'ttFlavor': flavor,
    }]}
    for sp in cd.get('spells', []):
        key = sp['spellKey'].upper()
        max_level = int(sp.get('maxLevel') or 5)
        cds = numeric(sp.get('cooldownCoefficients'), max_level) or numeric(sp.get('cooldown'), max_level)
        costs = numeric(sp.get('costCoefficients'), max_level) or numeric(sp.get('cost'), max_level)
        main, rules, flavor = texts[key]
        spell = {
            'name': sp.get('name', ''),
            'icon': icon_url(sp.get('abilityIconPath')),
            'cooldown': {'modifiers': [{'values': cds, 'units': ['']}]} if cds else None,
            'cost': {'modifiers': [{'values': costs, 'units': ['']}]} if costs else None,
            'effects': [{'description': main, 'leveling': []}],
            'ttNotes': rules, 'ttFlavor': flavor,
        }
        ammo = sp.get('ammo') or {}
        max_ammo = ammo.get('maxAmmo') if isinstance(ammo, dict) else None
        if isinstance(max_ammo, (int, float)) and max_ammo > 1:
            spell['charges'] = max_ammo
        abilities[key] = [spell]
    return {'name': cd['name'], 'title': cd.get('title', ''), 'abilities': abilities,
            '_source': 'communitydragon'}


def get_cd_champion(num_id, lang='en'):
    return cached(f'cd:{lang}:{num_id}', lambda: fetch_locale(f'champions/{num_id}.json', lang))


def norm_text(s):
    return re.sub(r'\W+', '', (s or '').lower())


def strip_text(text, snippet):
    """Quita `snippet` de `text` (tolerando saltos de línea/espacios distintos). Devuelve (texto, ¿quitado?)."""
    words = snippet.split()
    if not words:
        return text, False
    pat = re.compile(r'\s+'.join(re.escape(w) for w in words), re.I)
    new, n = pat.subn('', text, count=1)
    return (re.sub(r'\n{3,}', '\n\n', new).strip(), True) if n else (text, False)


def enrich_with_cdragon(data, num_id, lang='en'):
    """Añade a los datos de Meraki las notas en cursiva y la ambientación del tooltip del juego.

    Si Meraki ya incluye ese texto dentro de la descripción, se retira de allí para que
    aparezca una sola vez, con el formato de nota."""
    try:
        texts = cd_spell_texts(get_cd_champion(num_id))
    except Exception as e:
        print(f'Notas de CommunityDragon no disponibles ({e})')
        return
    print(f'Tooltip CD {num_id}: ' + ', '.join(
        f'{k}: {len(r)} notas{" + ambientación" if fl else ""}' for k, (_m, r, fl) in texts.items()))

    def effects_of(forms):
        return [e for f in forms for e in f.get('effects') or []]

    def remove_everywhere(forms, snippet):
        removed = False
        for e in effects_of(forms):
            e['description'], ok = strip_text(e.get('description') or '', snippet)
            removed = removed or ok
        return removed

    loc = {}
    if lang != 'en':
        try:
            loc = cd_spell_texts(get_cd_champion(num_id, lang))
        except Exception as e:
            print(f'Idioma {lang} no disponible para notas ({e})')

    for key, (_main, rules, flavor) in texts.items():
        forms = (data.get('abilities') or {}).get(key)
        if not forms:
            continue
        notes = []
        for r in rules:
            removed = remove_everywhere(forms, r)
            present = norm_text(' '.join(e.get('description') or '' for e in effects_of(forms)))
            if removed or norm_text(r) not in present:
                notes.append(r)
        # texto mostrado: el del idioma elegido si encaja 1 a 1 con el inglés (que se usa para quitar duplicados)
        l_rules, l_flavor = (loc.get(key, (None, [], ''))[1:] if loc else ([], ''))
        if notes and len(l_rules) == len(rules):
            notes = [l_rules[rules.index(n)] for n in notes]
        if notes:
            forms[0]['ttNotes'] = notes
        if flavor:
            remove_everywhere(forms, flavor)
            forms[0]['ttFlavor'] = l_flavor or flavor


def localize_names(data, num_id, lang):
    """Nombre, título y nombres de habilidad en el idioma elegido (los textos de Meraki siguen en inglés)."""
    if lang == 'en':
        return
    try:
        cd = get_cd_champion(num_id, lang)
    except Exception as e:
        print(f'Nombres en {lang} no disponibles ({e})')
        return
    data['name'] = cd.get('name') or data.get('name')
    data['title'] = cd.get('title') or data.get('title')
    names = {'P': (cd.get('passive') or {}).get('name')}
    names.update({sp['spellKey'].upper(): sp.get('name') for sp in cd.get('spells', [])})
    for key, forms in (data.get('abilities') or {}).items():
        if forms and names.get(key):
            forms[0]['name'] = names[key]


def get_champion(alias, num_id, lang='en'):
    def load():
        try:
            data = fetch_json(f'{MERAKI}/{alias}.json')
            data['_source'] = 'meraki'
            enrich_with_cdragon(data, num_id, lang)
            localize_names(data, num_id, lang)
            return data
        except Exception as e:
            print(f'Meraki no disponible para {alias} ({e}); usando CommunityDragon')
        # Respaldo en inglés (default) para que el parseo del cliente sea consistente con Meraki
        data = adapt_cdragon(get_cd_champion(num_id), num_id)
        localize_names(data, num_id, lang)
        return data
    return cached(f'champ:{lang}:{alias}:{num_id}', load)


def debug_champion(num_id):
    """Textos crudos de CommunityDragon (para revisar etiquetas y variables sin resolver)."""
    cd = get_cd_champion(num_id)
    out = {'P': {'description': (cd.get('passive') or {}).get('description')}}
    for sp in cd.get('spells', []):
        out[sp['spellKey'].upper()] = {
            'dynamicDescription': sp.get('dynamicDescription'),
            'effectAmounts': sp.get('effectAmounts'),
            'coefficients': sp.get('coefficients'),
            'keys': sorted(sp.keys()),
        }
    return out


def list_icons():
    if not ICONS_DIR.is_dir():
        return []
    return sorted(p.stem for p in ICONS_DIR.glob('*.png') if p.stat().st_size > 100)


# ---------------------------------------------------------------- HTTP
CHAMP_RE = re.compile(r'^/api/champion/([A-Za-z0-9]+)_(\d+)$')
DEBUG_RE = re.compile(r'^/api/debug/(\d+)$')


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        lang = (parse_qs(parsed.query).get('lang') or ['en'])[0]
        lang = lang if lang in LOCALE_FOLDERS else 'en'
        try:
            if path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
            elif path == '/api/icons':
                self.send_json(list_icons())
            elif path == '/api/version':
                try:
                    self.send_json(cached('version', get_version))
                except Exception:
                    self.send_json({'patch': 'N/D'})
            elif path == '/api/list':
                self.send_json(cached(f'list:{lang}', lambda: get_champion_list(lang)))
            elif path.startswith('/api/champion/'):
                m = CHAMP_RE.match(path)
                if not m:
                    return self.send_json({'error': 'Ruta no válida'}, 400)
                self.send_json(get_champion(m.group(1), m.group(2), lang))
            elif DEBUG_RE.match(path):
                self.send_json(debug_champion(DEBUG_RE.match(path).group(1)))
            elif path.startswith('/api/'):
                self.send_json({'error': 'No encontrado'}, 404)
            else:
                super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print(f'Error en {path}: {e}')
            try:
                self.send_json({'error': str(e)}, 502)
            except Exception:
                pass


if __name__ == '__main__':
    if not list_icons():
        print('Aviso: ./icons está vacío. Ejecuta: python fetch_icons.py')
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(f'Servidor listo en http://{HOST}:{PORT} (Ctrl+C para salir)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
        sys.exit(0)