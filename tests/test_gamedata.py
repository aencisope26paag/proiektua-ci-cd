import pytest

import gamedata as g
from conftest import calc, named, number, stat_by_dv


# ------------------------------------------------------------ números
@pytest.mark.parametrize('value, decimals, expected', [
    (10.0, None, '10'), (52.49999, None, '52.5'), (0.1 + 0.2, None, '0.3'), (-0.0, None, '0'),
    (1.23456, 1, '1.2'), (7, 0, '7'),
])
def test_num_redondea_y_quita_ceros(value, decimals, expected):
    assert g.num(value, decimals) == expected


def test_num_list_colapsa_valores_iguales():
    assert g.num_list([5, 5, 5]) == '5'
    assert g.num_list([10, 20, 30]) == '10 / 20 / 30'


def test_ranks_salta_el_indice_cero():
    assert g.ranks([0, 10, 20, 30, 40, 50, 60], 5) == [10, 20, 30, 40, 50]
    assert g.ranks([1, 2, 3], 5) == [1, 2, 3]          # lista corta: se usa tal cual


# ------------------------------------------------------------ cálculos
def ctx_for(mini_bin, slot='Q'):
    return g.parse_bin(mini_bin)[slot]


def test_calculo_base_mas_estadistica(mini_bin):
    ctx = ctx_for(mini_bin)
    base, stats = g.eval_calc(ctx['calcs']['qdamage'], ctx)
    assert base == ('r', [10, 20, 30, 40, 50])
    assert stats[0]['stat'] == 'ad' and stats[0]['scope'] == 'bonus'
    assert stats[0]['val'] == ('r', [.5, .6, .7, .8, .9])


def test_calculo_modificado_multiplica_base_y_estadisticas(mini_bin):
    ctx = ctx_for(mini_bin)
    base, stats = g.eval_calc(ctx['calcs']['qedgedamage'], ctx)
    assert base[1] == [15, 30, 45, 60, 75]
    assert stats[0]['val'][1][0] == pytest.approx(.75)


def test_interpolacion_por_nivel_cubre_18_niveles(mini_bin):
    ctx = ctx_for(mini_bin, 'P')
    kind, vals = g.eval_calc(ctx['calcs']['pcooldown'], ctx)[0]
    assert kind == 'l' and len(vals) == 18
    assert vals[0] == pytest.approx(22) and vals[-1] == pytest.approx(10)


def test_breakpoints_son_escalones():
    ctx = {'dv': {}, 'calcs': {}, 'n': 5, 'effects': []}
    part = {'__type': 'ByCharLevelBreakpointsCalculationPart', 'mLevel1Value': .55,
            'mBreakpoints': [{'mLevel': 6, 'mAdditionalBonusAtThisLevel': .05},
                             {'mLevel': 11, 'mAdditionalBonusAtThisLevel': .05}]}
    _kind, vals = g.eval_part(part, ctx)
    assert vals[0] == pytest.approx(.55) and vals[4] == pytest.approx(.55)
    assert vals[5] == pytest.approx(.60) and vals[10] == pytest.approx(.65)


def test_multiplicador_a_nivel_de_calculo():
    ctx = {'dv': {'base': [0, 16, 16, 16, 16, 16], 'ratio': [0, .013] * 3}, 'calcs': {}, 'n': 5, 'effects': []}
    c = calc([named('Base'), stat_by_dv('Ratio', 12, formula=2)], mMultiplier=number(0.01))
    base, stats = g.eval_calc(c, ctx)
    assert base[1][0] == pytest.approx(.16)
    assert stats[0]['stat'] == 'hp' and stats[0]['val'][1][0] == pytest.approx(.00013)


def test_parte_desconocida_lanza_unsupported():
    with pytest.raises(g.Unsupported):
        g.eval_part({'__type': 'AlgoRaroCalculationPart'}, {'dv': {}, 'calcs': {}, 'n': 5})


def test_estadistica_desconocida_se_etiqueta_con_su_codigo():
    ctx = {'dv': {'r': [0, 1, 1, 1, 1, 1]}, 'calcs': {}, 'n': 5, 'effects': []}
    _b, stats = g.eval_calc(calc([stat_by_dv('R', 99)]), ctx)
    assert stats[0]['stat'] == 'stat99'


@pytest.mark.parametrize('stat, coefs, expected_vals, per', [
    ('ad', [.6, .7], [60, 70], False),               # coeficiente normal -> porcentaje
    ('hp', [.00013], [1.3], True),                   # diminuto -> "por cada 100"
    ('ap', [.0004], [4.0], True),
])
def test_stat_display(stat, coefs, expected_vals, per):
    vals, is_per = g.stat_display(stat, coefs)
    assert is_per is per
    assert vals == pytest.approx(expected_vals)


# ------------------------------------------------------------ variables y plantillas
def test_render_var_lista_multiplicador_y_decimales(mini_bin):
    ctx = ctx_for(mini_bin)
    assert g.render_var('QBaseDamage', ctx) == '10 / 20 / 30 / 40 / 50'
    assert g.render_var('QSlow*-100', ctx) == '20 / 25 / 30 / 35 / 40'
    assert g.render_var('QADRatio*100', ctx) == '50 / 60 / 70 / 80 / 90'
    assert g.render_var('QADRatio.1*100', ctx) == '50.0 / 60.0 / 70.0 / 80.0 / 90.0'   # ".1" = un decimal


def test_render_var_calculo_genera_marcas(mini_bin):
    out = g.render_var('QDamage', ctx_for(mini_bin))
    assert out == '10 / 20 / 30 / 40 / 50 (+ {{S|ad|bonus|50 / 60 / 70 / 80 / 90}})'


def test_render_var_nivel_genera_rango(mini_bin):
    assert g.render_var('PDamage*100', ctx_for(mini_bin, 'P')) == '{{L|4|10}}'


def test_variable_sin_resolver_devuelve_interrogante_y_se_registra(mini_bin):
    ctx = ctx_for(mini_bin)
    assert g.render_var('NoExiste', ctx) == '?'
    assert 'NoExiste' in ctx['unresolved'][0]


def test_modificadores_internos_se_eliminan(mini_bin):
    assert g.render_var('SpellModifierDescriptionAppend', ctx_for(mini_bin)) == ''


def test_render_template_convierte_etiquetas_y_saltos():
    ctx = {'dv': {}, 'calcs': {}, 'n': 5, 'effects': [], 'cooldown': None, 'mana': None}
    out = g.render_template('A <status>Stun</status><br>B <foo>x</foo> <keywordMajor>All <i>Out</i></keywordMajor>', ctx)
    assert out == 'A {{t:cc}}Stun{{/t}}\nB x {{t:kw}}All Out{{/t}}'


def test_split_template_separa_notas_y_ambientacion(mini_bin, mini_cd):
    raw = mini_cd['spells'][0]['dynamicDescription']
    main, rules, flavor = g.split_template(raw, ctx_for(mini_bin))
    assert 'Range grows' not in main and 'Hello' not in main
    assert rules == ['Range grows with size.']
    assert flavor == '"Hello."'


# ------------------------------------------------------------ etiquetas y filas
@pytest.mark.parametrize('name, dmg, expected', [
    ('QEdgeDamage', 'PHYSICAL_DAMAGE', 'Edge Physical Damage'),
    ('Calc_Passive_Damage', 'MAGIC_DAMAGE', 'Passive Magic Damage'),
    ('MagicDamageReduction', 'MAGIC_DAMAGE', 'Magic Damage Reduction'),     # no duplica "Magic"
    ('TotalWShield', None, 'Shield'),                                        # sin 'Total' ni letra de tecla
    ('Calc_Minion_Execute_Amp', None, 'Minion Execute Amp'),
])
def test_calc_label(name, dmg, expected):
    assert g.calc_label(name, dmg) == expected


def test_pct_used_detecta_variables_multiplicadas_por_100():
    assert g.pct_used('x @PhysReduction*100@% y @Other@ z @Spell.A:B.1*100@') == {'physreduction', 'b'}


def test_build_leveling_omite_hashes_y_agrega_filas_de_tabla(mini_bin):
    rows = g.build_leveling(ctx_for(mini_bin), 'PHYSICAL_DAMAGE')
    labels = [r['attribute'] for r in rows]
    assert 'Physical Damage' in labels and 'Edge Physical Damage' in labels
    assert not any(l.startswith('{') for l in labels)
    slow = next(r for r in rows if r['attribute'] == 'Slow')          # fila de la tabla no cubierta por cálculos
    assert slow['modifiers'][0]['values'] == [20, 25, 30, 35, 40]
    dmg = next(r for r in rows if r['attribute'] == 'Physical Damage')
    assert dmg['modifiers'][1]['units'] == ['% bonus AD']


def test_porcentaje_por_nombre_con_fraccion():
    ctx = {'dv': {'x': [0, .125, .15, .175, .2, .225]}, 'calcs': {}, 'n': 5, 'effects': [],
           'own_calcs': {'physicaldamagereduction': calc([named('X')])},
           'calc_names': {'physicaldamagereduction': 'PhysicalDamageReduction'}, 'rows': []}
    row = g.calc_rows(ctx, None)[0][0]
    assert row['modifiers'][0]['values'][:2] == [12.5, 15.0] and row['modifiers'][0]['units'] == ['%']


# ------------------------------------------------------------ campeón completo
def test_build_champion_estructura(mini_bin, mini_cd):
    data = g.build_champion(mini_bin, mini_cd, lambda p: 'ICON:' + p.split('/')[-1])   # icon_url simulado
    assert data['_source'] == 'gamedata' and data['name'] == 'Mini'
    assert set(data['abilities']) == {'P', 'Q', 'W'}
    q = data['abilities']['Q'][0]
    assert q['icon'] == 'ICON:Q.png' and q['damageType'] == 'PHYSICAL_DAMAGE'
    assert q['cooldown']['modifiers'][0]['values'] == [10, 9, 8, 7, 6]
    assert q['cost']['modifiers'][0]['values'] == [50, 55, 60, 65, 70] and q['costType'] == 'Mana'
    assert q['ttNotes'] == ['Range grows with size.']
    assert '{{t:phys}}' in q['effects'][0]['description']


def test_pasiva_con_enfriamiento_por_nivel(mini_bin, mini_cd):
    p = g.build_champion(mini_bin, mini_cd, lambda p: p)['abilities']['P'][0]
    values = p['cooldown']['modifiers'][0]['values']
    assert len(values) == 18 and values[0] == 22 and values[-1] == 10


def test_huecos_sin_resolver_quedan_registrados(mini_bin, mini_cd):
    data = g.build_champion(mini_bin, mini_cd, lambda p: p)
    assert 'W' in data['_unresolved'] and 'Nope' in data['_unresolved']['W'][0]
    assert 'Q' not in data['_unresolved']


def test_campeon_sin_habilidades_lanza_error(mini_cd):
    doc = {'Characters/X/CharacterRecords/Root': {'spellNames': []}}
    with pytest.raises(g.Unsupported):
        g.build_champion(doc, mini_cd, lambda p: p)
