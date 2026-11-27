"""Pruebas de la API del servidor. No usan internet: `server.fetch_json` se sustituye por datos de ejemplo."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server


# ------------------------------------------------------------ utilidades puras
def test_public_patch_suma_diez_a_la_version_interna():
    assert server.public_patch('16.22.123.456') == '26.22'
    assert server.public_patch('9.4.1') == '9.4'              # versiones antiguas no se tocan


def test_flat_numbers_aplana_y_extrae_de_textos():
    assert server.flat_numbers([[0, 12], [11, 10], None, True, 'x']) == [0, 12, 11, 10]
    assert server.flat_numbers('9 / 8.5 / 8') == [9.0, 8.5, 8.0]
    assert server.flat_numbers(None) == []


def test_strip_text_tolera_saltos_de_linea():
    text, ok = server.strip_text('Hit.\n\nThe range\ngrows with size.', 'The range grows with size.')
    assert ok and text == 'Hit.'
    assert server.strip_text('Hit.', 'Otra cosa') == ('Hit.', False)


def test_clean_description_resuelve_variables_y_marca_huecos():
    variables = server.build_vars({'effectAmounts': {'Effect1Amount': [0, 60, 100]}}, 2)   # quita el hueco del índice 0
    out = server.clean_description('Deals @Effect1Amount@ <b>dmg</b> and @Missing@.<br>End', variables)
    assert out == 'Deals 60 / 100 dmg and ?.\nEnd'


def test_adapt_cdragon_tolera_listas_anidadas():
    cd = {'name': 'N', 'title': 't', 'passive': {'name': 'P', 'description': 'x'},
          'spells': [{'spellKey': 'q', 'name': 'Q', 'maxLevel': 5, 'cooldownCoefficients': [[0, 12], [11, 10]],
                      'costCoefficients': [0, 50, 50], 'ammo': {'maxAmmo': [1, 2]}}]}
    q = server.adapt_cdragon(cd, '1')['abilities']['Q'][0]
    assert q['cooldown']['modifiers'][0]['values'] == [12, 11, 10]
    assert 'charges' not in q                                  # maxAmmo no numérico: se ignora


def test_fetch_json_no_reintenta_errores_http(monkeypatch):
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise urllib.error.HTTPError('u', 404, 'nf', {}, None)
    monkeypatch.setattr(server.urllib.request, 'urlopen', boom)
    with pytest.raises(urllib.error.HTTPError):
        server.fetch_json('http://x')
    assert len(calls) == 1


def test_fetch_json_reintenta_una_vez_los_timeouts(monkeypatch):
    calls = []

    def slow(*a, **k):
        calls.append(1)
        raise TimeoutError('lento')
    monkeypatch.setattr(server.urllib.request, 'urlopen', slow)
    with pytest.raises(TimeoutError):
        server.fetch_json('http://x')
    assert len(calls) == 2


# ------------------------------------------------------------ API HTTP con servidor real en un hilo
SUMMARY = [{'id': 1, 'alias': 'Mini', 'name': 'Mini'}, {'id': 2000, 'alias': 'Skin', 'name': 'No campeón'}]
MERAKI_MINI = {'name': 'Mini', 'title': 'Meraki', 'abilities': {'Q': [{'name': 'Q', 'effects': [
    {'description': 'Meraki text', 'leveling': []}]}]}}


@pytest.fixture
def api(monkeypatch, mini_bin, mini_cd):
    state = {'bin_ok': True, 'urls': []}

    def fake_fetch(url, timeout=30, retries=1):
        state['urls'].append(url)
        if url.endswith('champion-summary.json'):
            return SUMMARY
        if url.endswith('content-metadata.json'):
            return {'version': '16.22.1.1'}
        if url.endswith('/mini/mini.bin.json'):
            if not state['bin_ok']:
                raise urllib.error.HTTPError(url, 404, 'nf', {}, None)
            return mini_bin
        if '/champions/1.json' in url:
            return mini_cd
        if 'merakianalytics' in url and url.endswith('/Mini.json'):
            return json.loads(json.dumps(MERAKI_MINI))
        raise urllib.error.HTTPError(url, 404, 'nf', {}, None)

    monkeypatch.setattr(server, 'fetch_json', fake_fetch)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True).start()
    base = f'http://127.0.0.1:{httpd.server_address[1]}'

    def get(path):
        try:
            with urllib.request.urlopen(base + path, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    get.state = state
    yield get
    httpd.shutdown()
    httpd.server_close()


def test_lista_filtra_ids_que_no_son_campeones(api):
    status, body = api('/api/list?lang=en')
    data = json.loads(body)['data']
    assert status == 200 and list(data) == ['Mini'] and data['Mini']['numId'] == 1


def test_version(api):
    assert json.loads(api('/api/version')[1]) == {'patch': '26.22', 'full': '16.22.1.1'}


def test_iconos_lista_los_png_del_proyecto(api):
    status, body = api('/api/icons')
    names = json.loads(body)
    assert status == 200 and {'ad', 'ap', 'hp', 'onhit'} <= set(names)


def test_campeon_desde_datos_del_juego(api):
    status, body = api('/api/champion/Mini_1?lang=en')
    data = json.loads(body)
    assert status == 200 and data['_source'] == 'gamedata'
    assert set(data['abilities']) == {'P', 'Q', 'W'}


def test_campeon_se_cachea(api):
    api('/api/champion/Mini_1')
    n = len(api.state['urls'])
    api('/api/champion/Mini_1')
    assert len(api.state['urls']) == n                          # la segunda vez no hay descargas nuevas


def test_respaldo_en_meraki_si_fallan_los_datos_del_juego(api):
    api.state['bin_ok'] = False
    data = json.loads(api('/api/champion/Mini_1')[1])
    assert data['_source'] == 'meraki'


def test_hueco_sin_resolver_se_completa_con_meraki_solo_en_esa_habilidad(api):
    data = json.loads(api('/api/champion/Mini_1')[1])
    w = data['abilities']['W'][0]                               # su plantilla tiene @Nope@ sin resolver
    assert '?' in w['effects'][0]['description'] or w.get('descSource') == 'meraki'
    q = data['abilities']['Q'][0]
    assert q.get('descSource') is None and q['rich'] is True    # la Q se resolvió entera: sigue con datos del juego


@pytest.mark.parametrize('path, status', [
    ('/api/champion/Mini', 400),            # falta el id numérico
    ('/api/champion/../etc_1', 400),        # intento de salirse de la ruta
    ('/api/nope', 404),
    ('/', 200),                             # sirve index.html
    ('/app.js', 200),
])
def test_rutas_y_errores(api, path, status):
    assert api(path)[0] == status


def test_idioma_no_valido_cae_a_ingles(api):
    assert api('/api/list?lang=xx')[0] == 200
