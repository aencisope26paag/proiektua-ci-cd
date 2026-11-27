'use strict';

/* ======================================================================
 *  Textos de la interfaz. Para añadir un idioma: copia este objeto en LANGS.
 * ==================================================================== */
const LANGS = {
  es: {
    post: true, // en español el modificador va detrás: "vida adicional propia"
    cooldown: 'Enfriamiento', recharge: 'Recarga', passive: 'Pasiva', cost: 'Coste', noCost: 'Sin coste',
    charges: 'Cargas', lvl: 'nv.', lastChanged: 'Último cambio: Parche', loadingChamp: 'Cargando datos de habilidades...',
    searchPlaceholder: "Buscar campeón (ej. K'Sante, Aatrox, Zed, Tahm Kench)...",
    errList: 'Error cargando la lista de campeones', errChamp: 'No se pudo cargar',
    footer: 'Datos del cliente: Parche', fallbackNote: 'Datos de respaldo (CommunityDragon): sin desglose de escalados.',
    per: 'por cada', note: 'Nota',
    descNote: 'Las descripciones aún están en inglés (fuente: Meraki). Nombres, notas, etiquetas y cifras ya están traducidos.',
    units: { second: 's', seconds: 's', units: 'uds.' },
    attrs: {
      'damage': 'Daño', 'magic damage': 'Daño mágico', 'physical damage': 'Daño físico', 'true damage': 'Daño verdadero',
      'total damage': 'Daño total', 'bonus damage': 'Daño adicional', 'minimum damage': 'Daño mínimo',
      'maximum damage': 'Daño máximo', 'bonus magic damage': 'Daño mágico adicional',
      'bonus physical damage': 'Daño físico adicional', 'bonus true damage': 'Daño verdadero adicional',
      'total magic damage': 'Daño mágico total', 'total physical damage': 'Daño físico total',
      'damage per second': 'Daño por segundo', 'damage reduction': 'Reducción de daño',
      'heal': 'Curación', 'healing': 'Curación', 'total heal': 'Curación total', 'increased healing': 'Curación aumentada',
      'heal amount': 'Cantidad de curación', 'bonus healing': 'Curación adicional',
      'shield': 'Escudo', 'shield strength': 'Fuerza del escudo', 'shield amount': 'Cantidad de escudo',
      'total shield': 'Escudo total', 'slow': 'Ralentización', 'cooldown': 'Enfriamiento',
      'cooldown reduction': 'Reducción de enfriamiento', 'cooldown refund': 'Reembolso de enfriamiento',
      'mana cost': 'Coste de maná', 'energy cost': 'Coste de energía', 'cost': 'Coste', 'mana restored': 'Maná restaurado',
      'range': 'Alcance', 'cast range': 'Alcance de lanzamiento', 'duration': 'Duración',
      'stun duration': 'Duración del aturdimiento', 'slow duration': 'Duración de la ralentización',
      'shield duration': 'Duración del escudo', 'root duration': 'Duración de la inmovilización',
      'movement speed': 'Velocidad de movimiento', 'bonus movement speed': 'Velocidad de movimiento adicional',
      'attack speed': 'Velocidad de ataque', 'bonus attack speed': 'Velocidad de ataque adicional',
      'attack damage': 'Daño de ataque', 'bonus attack damage': 'Daño de ataque adicional',
      'ability power': 'Poder de habilidad', 'armor': 'Armadura', 'bonus armor': 'Armadura adicional',
      'magic resistance': 'Resistencia mágica', 'bonus magic resistance': 'Resistencia mágica adicional',
      'armor reduction': 'Reducción de armadura', 'magic resistance reduction': 'Reducción de resistencia mágica',
      'health': 'Vida', 'bonus health': 'Vida adicional', 'maximum health': 'Vida máxima',
      'critical strike chance': 'Prob. de golpe crítico', 'critical strike damage': 'Daño de golpe crítico',
      'damage amplification': 'Amplificación de daño', 'bonus damage amplification': 'Amplificación de daño adicional',
    },
    owner: { self: 'propia', target: 'del objetivo' },
    scope: { base: 'base', bonus: 'adicional', total: 'total', max: 'máx.', missing: 'faltante', current: 'actual' },
    stat: {
      ad: 'AD', ap: 'AP', as: 'vel. de ataque', crit: 'crítico', lethality: 'letalidad', magicpen: 'pen. mágica',
      hp: 'vida', hpregen: 'reg. de vida', armor: 'armadura', mr: 'RM', tenacity: 'tenacidad', mana: 'maná',
      energy: 'energía', haste: 'celeridad', ms: 'vel. de mov.', range: 'alcance', vamp: 'robo de vida',
      heal: 'curación', shield: 'escudo', onhit: 'on-hit',
    },
  },
  en: {
    post: false,
    cooldown: 'Cooldown', recharge: 'Recharge', passive: 'Passive', cost: 'Cost', noCost: 'No cost',
    charges: 'Charges', lvl: 'lvl', lastChanged: 'Last changed: Patch', loadingChamp: 'Loading ability data...',
    searchPlaceholder: "Search champion (e.g. K'Sante, Aatrox, Zed, Tahm Kench)...",
    errList: 'Error loading champion list', errChamp: 'Could not load',
    footer: 'Client data: Patch', fallbackNote: 'Fallback data (CommunityDragon): no scaling breakdown.',
    per: 'per', note: 'Note', descNote: '', units: {}, attrs: {},
    owner: { self: 'own', target: "target's" },
    scope: { base: 'base', bonus: 'bonus', total: 'total', max: 'max', missing: 'missing', current: 'current' },
    stat: {
      ad: 'AD', ap: 'AP', as: 'attack speed', crit: 'crit', lethality: 'lethality', magicpen: 'magic pen',
      hp: 'health', hpregen: 'health regen', armor: 'armor', mr: 'MR', tenacity: 'tenacity', mana: 'mana',
      energy: 'energy', haste: 'haste', ms: 'move speed', range: 'range', vamp: 'vamp', heal: 'heal',
      shield: 'shield', onhit: 'on-hit',
    },
  },
};
const DEFAULT_LANG = 'en';
let currentLang = DEFAULT_LANG;
let T = LANGS[DEFAULT_LANG];
function setLang(code) {
  currentLang = LANGS[code] ? code : DEFAULT_LANG;
  T = LANGS[currentLang];
}

/** Nombre de atributo de Meraki en el idioma activo (si no hay traducción, se deja tal cual). */
function attrLabel(attr) {
  const key = String(attr || '').trim().replace(/:$/, '').toLowerCase();
  return (T.attrs && T.attrs[key]) || attr;
}

/* ======================================================================
 *  Clasificación de estadísticas (una única tabla para todo)
 *  El ORDEN importa: lo más específico va primero
 *  (p. ej. "armor penetration" antes que "armor", "health regen" antes que "health").
 * ==================================================================== */
const STAT_RULES = [
  ['magicpen', String.raw`magic\s+pen(?:etration)?`],
  ['lethality', String.raw`armou?r\s+pen(?:etration)?|lethality`],
  ['hpregen', String.raw`health\s+regen(?:eration)?`],
  ['mana', String.raw`mana\s+regen(?:eration)?`],
  ['crit', String.raw`crit(?:ical)?(?:\s+strike)?(?:\s+(?:chance|damage))?`],
  ['as', String.raw`attack\s+speed`],
  ['ap', String.raw`ability\s+power|AP`],
  ['ad', String.raw`attack\s+damage|AD`],
  ['haste', String.raw`ability\s+haste`],
  ['ms', String.raw`move(?:ment)?\s+speed`],
  ['range', String.raw`attack\s+range`],
  ['vamp', String.raw`omnivamp|life\s?steal|physical\s+vamp|spell\s+vamp`],
  ['onhit', String.raw`on-hit`],
  ['tenacity', 'tenacity'],
  ['mr', String.raw`magic\s+resist(?:ance)?|MR`],
  ['armor', String.raw`armou?r`],
  ['hp', String.raw`health|HP`],          // "bonus health" -> hp, nunca heal/vamp
  ['mana', 'mana'],
  ['energy', 'energy'],
  ['heal', String.raw`heal(?:ing|ed|s)?`], // después de hp: "health" no casa con \bheal\b
  ['shield', String.raw`shield(?:s|ing)?`],
];

const COMPILED_RULES = STAT_RULES.map(([type, src]) => [type, new RegExp(String.raw`\b(?:${src})\b`, 'i')]);

function classifyStat(text) {
  for (const [type, re] of COMPILED_RULES) if (re.test(text)) return type;
  return null;
}

// Modificadores: base / bonus / total / max / missing / current
const SCOPE_WORD = String.raw`(?:base|bonus|total|max(?:imum)?|missing|current)`;
const SCOPE_WORD_RE = new RegExp(String.raw`\b${SCOPE_WORD}\b`, 'gi');
const SCOPE_PRIORITY = ['missing', 'current', 'max', 'bonus', 'base', 'total'];

function scopeOf(text) {
  const found = new Set((text.match(SCOPE_WORD_RE) || []).map(w => {
    w = w.toLowerCase();
    return w.startsWith('max') ? 'max' : w;
  }));
  return SCOPE_PRIORITY.find(s => found.has(s)) || null;
}

const ATTR_CC_RE = /\b(slow|stun|root|snare|silence|fear|charm|taunt|suppress|knock|airborne|sleep)/i;

/** 'phys' | 'magic' | 'true' | null a partir de un texto ("Magic Damage", "MAGIC_DAMAGE"...). */
function damageKind(text) {
  const a = String(text || '').toLowerCase();
  if (/true/.test(a)) return 'true';
  if (/physical/.test(a)) return 'phys';
  if (/magic/.test(a)) return 'magic';
  return null;
}

/** Color de un valor "propio" (daño, curación, escudo...) a partir del nombre del atributo. */
function classifyAttribute(attr, spellDamageType = '') {
  const a = attr.toLowerCase();
  if (/true\s+damage/.test(a)) return 'true';
  if (/physical\s+(?:damage|dmg)/.test(a)) return 'phys';
  if (/magic(?:al)?\s+(?:damage|dmg)/.test(a)) return 'magic';
  const stat = classifyStat(a);
  if (stat) return stat;
  if (/damage/.test(a)) return damageKind(spellDamageType) || 'base';  // "Damage" a secas: usa el tipo de la habilidad
  if (ATTR_CC_RE.test(a)) return 'cc';
  return 'base';
}

/* ---- ¿De quién es la vida? propia (self) vs del objetivo (target) ---- */
const OWNER_TARGET_RE = /\b(?:target|enemy|enemies|victim)['\u2019]?s?\b/i;
const OWNER_SELF_RE = /\b(?:his|her|its|own|your)\b/i;   // "their" es ambiguo: se decide por contexto
const OWNER_STRIP_RE = /\b(?:of|the|target['\u2019]?s|enemy['\u2019]?s|his|her|their|its|your|own)\b/gi;

/* ======================================================================
 *  Formato de números
 * ==================================================================== */
const round2 = n => Math.round(n * 100) / 100;

function formatValues(values) {
  const vals = (values || []).filter(v => v !== null && v !== undefined && v !== '');
  if (!vals.length) return { text: '', levels: 0 };
  const nums = vals.map(Number);
  const shown = nums.every(Number.isFinite) ? nums.map(round2) : vals.map(String);
  if (new Set(shown).size === 1) return { text: String(shown[0]), levels: 0 };
  if (shown.length >= 10) return { text: `${shown[0]}–${shown[shown.length - 1]}`, levels: shown.length };
  return { text: shown.join(' / '), levels: 0 };
}

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/** "AP per 100 bonus health" -> { main:'AP', n:'100', scope:'bonus', type:'hp' };  "per 100 AP" -> main vacío */
const PER_RE = /^(.*?)\s*\bper\s+(\d+)\s+(.+)$/i;
function parseDriver(text) {
  const m = text.match(PER_RE);
  if (!m) return null;
  const type = classifyStat(m[3].replace(OWNER_STRIP_RE, ''));
  return type ? { main: m[1], n: m[2], scope: scopeOf(m[3]), type } : null;
}

const cleanStat = t => t.replace(OWNER_STRIP_RE, '').replace(SCOPE_WORD_RE, '').replace(/\s+/g, ' ').trim();

/** Escalado entre paréntesis dentro de una unidad: "+ 7% per 100 AP", "+ 1.25% AP per 100 bonus health" */
function parseInner(body) {
  const m = body.match(/^\s*\+?\s*(\d+(?:\.\d+)?(?:\s*\/\s*\d+(?:\.\d+)?)*)\s*(%)?\s*(.*)$/i);
  if (!m) return null;
  const base = { value: m[1].replace(/\s+/g, ' '), symbol: m[2] || '' };
  const d = parseDriver(m[3]);
  if (d) {
    const mainType = d.main.trim() ? classifyStat(cleanStat(d.main)) : null;
    return { ...base, type: mainType || d.type, scope: mainType ? scopeOf(d.main) : null,
             per: { n: d.n, scope: d.scope, type: d.type, colored: !!mainType } };
  }
  const type = classifyStat(cleanStat(m[3]));
  return type ? { ...base, type, scope: scopeOf(m[3]), per: null } : null;
}

/** "% (+ 7% per 100 AP) of target's maximum health" ->
 *  { symbol:'%', scope:'max', owner:'target', type:'hp', inner:[...], per:null } */
function parseUnit(unit, isDamage = false) {
  const m = String(unit || '').match(/^\s*(%)?\s*(.*)$/);
  const symbol = m[1] || '';
  const inner = [];
  // los paréntesis con un escalado propio se extraen para que no contaminen la estadística principal
  const raw = m[2].replace(/\(([^)]*)\)/g, (all, body) => {
    const p = parseInner(body);
    if (!p) return all;
    inner.push(p);
    return ' ';
  });
  const d = parseDriver(raw);
  const per = d ? { n: d.n, scope: d.scope, type: d.type, colored: !!d.main.trim() } : null;
  const main = d ? d.main : raw;
  const scope = scopeOf(main);
  const statText = cleanStat(main);
  const type = statText ? classifyStat(statText) : null;
  let owner = OWNER_TARGET_RE.test(main) ? 'target' : OWNER_SELF_RE.test(main) ? 'self' : null;
  if (type === 'hp' && !owner) owner = scope === 'bonus' ? 'self' : (isDamage ? 'target' : 'self');
  return { symbol, scope, owner, type, inner, per, extra: type || per ? '' : statText };
}

/* ======================================================================
 *  Chips
 * ==================================================================== */
let availableIcons = new Set();

function iconHtml(type) {
  return availableIcons.has(type) ? `<img src="/icons/${type}.png" class="stat-icon" alt="">` : '';
}

/** icon: false | true (icono del propio tipo) | 'tipo' (icono de otro tipo) */
function chip(inner, type, { scope = null, icon = false, owner = null } = {}) {
  const cls = ['stat-chip', type, scope ? `scope-${scope}` : '', owner ? `owner-${owner}` : ''].filter(Boolean).join(' ');
  const iconType = icon === true ? type : icon;
  return `<span class="${cls}">${iconType ? iconHtml(iconType) : ''}${inner}</span>`;
}

/** Orden natural según idioma: "bonus AD" / "AD adicional"; "target's max health" / "vida máx. del objetivo". */
function statPhrase({ owner = null, scope = null, stat = '' }) {
  const o = owner ? T.owner[owner] : '';
  const sc = scope ? `<small class="scope-tag">${T.scope[scope]}</small>` : '';
  return (T.post ? [stat, sc, o] : [o, sc, stat]).filter(Boolean).join(' ');
}

/** " per 100 bonus health" (la estadística-motor, coloreada si el chip ya tiene otra estadística principal) */
function perHtml(per) {
  const phrase = statPhrase({ scope: per.scope, stat: T.stat[per.type] });
  return ` ${T.per} ${esc(per.n)} ${per.colored ? `<span class="${per.type}">${phrase}</span>` : phrase}`;
}

function formulaChip(mod, idx, attribute, spellDamageType = '') {
  const unit = (mod.units && mod.units[0]) || '';
  const u = parseUnit(unit, /damage/i.test(attribute));
  const attrType = classifyAttribute(attribute, spellDamageType);
  // Valor propio (idx 0): color por tipo de daño/efecto. Escalados: color por la estadística de origen.
  const mainType = u.type || (u.per ? u.per.type : null);
  let type = mainType || (idx === 0 ? attrType : 'base');
  // % de la vida del OBJETIVO: se pinta como el daño que causa (mágico = celeste), no como vida propia
  const targetHp = u.type === 'hp' && u.owner === 'target';
  if (targetHp) type = ['phys', 'magic', 'true'].includes(attrType) ? attrType : 'target';
  const { text, levels } = formatValues(mod.values);

  let inner = esc(text) + esc(u.symbol);
  u.inner.forEach(p => {
    const label = `${esc(p.value)}${esc(p.symbol)} ${statPhrase({ scope: p.scope, stat: T.stat[p.type] })}`
      + (p.per ? perHtml(p.per) : '');
    inner += ` (+ ${chip(label, p.type, { scope: p.scope, icon: true })})`;
  });
  if (u.type) {
    const showOwner = u.owner && (u.type === 'hp' || u.owner === 'target') ? u.owner : null;
    inner += ' ' + statPhrase({ owner: showOwner, scope: u.scope, stat: T.stat[u.type] });
  } else if (u.extra) {
    inner += ` ${esc(T.units[u.extra.toLowerCase()] ?? u.extra)}`;
  }
  if (u.per) inner += perHtml(u.per);
  if (levels) inner += ` <span class="lvl-tag">(${T.lvl} 1-${levels})</span>`;

  const html = chip(inner, type, {
    scope: u.scope, owner: u.type ? u.owner : null,
    icon: mainType && !targetHp ? mainType : false,
  });
  return idx === 0 ? html : `(+ ${html})`;
}

/* ======================================================================
 *  Descripciones: una sola pasada (sin re-procesar HTML ya generado)
 * ==================================================================== */
const STAT_SRC = STAT_RULES.map(r => r[1]).join('|');
const NUM = String.raw`\d+(?:\.\d+)?`;
const NUM_LIST = String.raw`${NUM}(?:\s*\/\s*${NUM})*%?`;
const OWNER = String.raw`(?:of\s+(?:his|her|their|its|your|the\s+target's|target's|the\s+enemy's|an\s+enemy's)\s+)?`;
const SCOPES = String.raw`(?:${SCOPE_WORD}\s+)*`;
const CC_SRC = String.raw`knock(?:s|ed|ing)?\s+(?:back|up|aside|airborne)|knockback|knockup|stun(?:s|ned|ning)?|root(?:s|ed|ing)?|snare[sd]?|slow(?:s|ed|ing)?|silenc(?:e|es|ed|ing)|fear(?:s|ed|ing)?|flee(?:s|ing)?|charm(?:s|ed|ing)?|taunt(?:s|ed|ing)?|suppress(?:es|ed|ion|ing)?|sleep(?:s|ing)?|airborne|polymorph(?:s|ed)?|disarm(?:s|ed)?`;

const DESC_RE = new RegExp([
  String.raw`(?<![\w.])(${NUM_LIST}\s*${OWNER}${SCOPES}(?:${STAT_SRC}))\b`,            // 1: escalado con número
  String.raw`\b((?:bonus\s+)?(?:physical|magic|true)\s+damage)\b`,                      // 2: tipo de daño
  String.raw`\b(${SCOPES}(?:${STAT_SRC}))\b`,                                           // 3: estadística suelta
  String.raw`\b(${CC_SRC})\b`,                                                          // 4: control de masas
  String.raw`(?<![\w.])(${NUM}(?:\s*\/\s*${NUM})+%?)`,                                  // 5: lista de números
].join('|'), 'gi');

/** Tipo/propietario de un escalado de la descripción. La vida "máxima/actual/faltante" sin dueño
 *  explícito es del objetivo si la frase habla de daño, y propia en el resto (curas, escudos). */
function descChip(scaled, after) {
  const type = classifyStat(scaled) || 'base';
  if (type !== 'hp') return { type, owner: null };
  const scope = scopeOf(scaled);
  const sentence = after.split(/[.\n]/)[0].slice(0, 90);
  const kind = (sentence.match(/\b(physical|magic|true)\s+damage\b/i) || [])[1];
  const owner = OWNER_TARGET_RE.test(scaled) ? 'target'
    : OWNER_SELF_RE.test(scaled) ? 'self'
    : scope === 'bonus' ? 'self'
    : kind ? 'target' : 'self';
  return owner === 'target' ? { type: damageKind(kind) || 'target', owner } : { type, owner };
}

function highlightDescription(text) {
  if (!text) return '';
  return esc(text).replace(DESC_RE, (m, scaled, dmg, stat, cc, list, offset, str) => {
    if (scaled) {
      const d = descChip(scaled, str.slice(offset + m.length));
      return chip(scaled, d.type, { scope: scopeOf(scaled), icon: d.owner !== 'target', owner: d.owner });
    }
    if (dmg) {
      const k = damageKind(dmg);
      return `<strong class="${k}">${dmg}</strong>`;
    }
    if (stat) return chip(stat, classifyStat(stat) || 'base', { scope: scopeOf(stat) });
    if (cc) return `<span class="cc">${cc}</span>`;
    if (list) return `<strong class="base">${list}</strong>`;
    return m;
  }).replace(/\n/g, '<br>');
}

/* ======================================================================
 *  Cooldown / coste
 * ==================================================================== */
function metaValue(block) {
  const mod = block && block.modifiers && block.modifiers[0];
  return mod ? { ...formatValues(mod.values), allZero: (mod.values || []).every(v => Number(v) === 0) } : null;
}

function cooldownText(spell, key) {
  const v = metaValue(spell.cooldown);
  if (!v || !v.text || v.allZero) return key === 'P' ? T.passive : '—';
  return `${esc(v.text)}s${v.levels ? ` <span class="lvl-tag">(${T.lvl} 1-${v.levels})</span>` : ''}`;
}

function costHtml(spell) {
  const v = metaValue(spell.cost);
  if (!v || !v.text) return '';
  if (v.allZero) return '<span>${T.cost}: <strong>${T.noCost}</strong></span>';
  const type = classifyStat(spell.costType || '') || 'base';
  const label = spell.costType && !/no\s+cost/i.test(spell.costType) ? ` ${esc(spell.costType)}` : '';
  return `<span>${T.cost}: <strong>${chip(esc(v.text) + label, type, { icon: type !== 'base' })}</strong></span>`;
}

/* ======================================================================
 *  Render
 * ==================================================================== */
/** Meraki ya da la versión pública ("V25.05"): solo se quita la "V". */
function publicPatch(raw) {
  return String(raw).replace(/^V/i, '');
}

function renderSpell(spell, key) {
  const formulas = [];
  const descriptions = [];

  (spell.effects || []).forEach(eff => {
    if (eff.description) descriptions.push(`<p class="desc">${highlightDescription(eff.description)}</p>`);
    (eff.leveling || []).forEach(lvl => {
      const parts = (lvl.modifiers || []).map((m, i) => formulaChip(m, i, lvl.attribute || '', spell.damageType)).join(' ');
      formulas.push(`<div class="formula-line"><span class="formula-label">${esc(attrLabel(lvl.attribute))}:</span> ${parts}</div>`);
    });
  });

  const notes = (Array.isArray(spell.ttNotes) ? spell.ttNotes : []).map(n => `<p class="note"><span class="note-label">${T.note}</span>${esc(n).replace(/\n/g, '<br>')}</p>`).join('');
  const flavor = typeof spell.ttFlavor === 'string' && spell.ttFlavor ? `<p class="flavor">${esc(spell.ttFlavor)}</p>` : '';
  const charges = spell.charges ? `<span>${T.charges}: <strong>${esc(spell.charges)}</strong></span>` : '';
  return `
    <div class="tooltip-card">
      <div class="tooltip-top">
        <div class="spell-id-group">
          <div class="spell-icon-wrap">
            <img src="${esc(spell.icon)}" alt="" onerror="this.style.display='none'">
            <span class="key-badge">${key}</span>
          </div>
          <div>
            <span class="spell-name">${esc(spell.name)}</span>
            <div class="spell-meta">
              <span>${charges ? T.recharge : T.cooldown}: <strong>${cooldownText(spell, key)}</strong></span>
              ${costHtml(spell)}${charges}
            </div>
          </div>
        </div>
      </div>
      ${formulas.length ? `<div class="shift-formulas">${formulas.join('')}</div>` : ''}
      ${descriptions.join('')}
      ${notes}${flavor}
    </div>`;
}

function renderChampion(champ, icon) {
  const patch = champ.patchLastChanged ? ` • ${T.lastChanged} ${publicPatch(champ.patchLastChanged)}` : '';
  const source = champ._source === 'communitydragon'
    ? `<p class="source-note">${T.fallbackNote}</p>` : '';
  const descNote = T.descNote && champ._source === 'meraki' ? `<p class="source-note">${T.descNote}</p>` : '';
  let html = `
    <div class="champ-header">
      <img src="${esc(icon)}" alt="${esc(champ.name)}">
      <div><h2>${esc(champ.name)}</h2><span>${esc(champ.title)}${patch}</span></div>
    </div>${source}${descNote}`;
  ['P', 'Q', 'W', 'E', 'R'].forEach(key => {
    (champ.abilities[key] || []).forEach(spell => { html += renderSpell(spell, key); });
  });
  return html;
}

/* ======================================================================
 *  UI (solo en navegador)
 * ==================================================================== */
if (typeof document !== 'undefined') {
  const searchInput = document.getElementById('searchInput');
  const suggestionsBox = document.getElementById('suggestions');
  const content = document.getElementById('content');
  let allChamps = [];
  let matches = [];
  let activeIdx = -1;
  let loadToken = 0;
  let currentChamp = null;
  const langSelect = document.getElementById('langSelect');
  const footer = document.getElementById('patchFooter');
  let patchText = '';

  const normalizeText = s => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/['.\-\s]/g, '');
  const showError = msg => { content.innerHTML = `<p class="error">${esc(msg)}</p>`; };

  async function getJson(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function loadChampion(champ) {
    const token = ++loadToken;
    content.innerHTML = `<p class="loading">${T.loadingChamp}</p>`;
    try {
      currentChamp = champ;
      const data = await getJson(`/api/champion/${champ.id}_${champ.numId}?lang=${currentLang}`);
      if (token !== loadToken) return; // llegó una petición más nueva
      content.innerHTML = renderChampion(data, champ.icon);
      history.replaceState(null, '', `#${champ.id}`);
    } catch (e) {
      if (token === loadToken) showError(`${T.errChamp} ${champ.name}: ${e.message}`);
    }
  }

  function closeSuggestions() {
    suggestionsBox.style.display = 'none';
    matches = []; activeIdx = -1;
  }

  function selectChampion(champ) {
    searchInput.value = '';
    closeSuggestions();
    loadChampion(champ);
  }

  function paintSuggestions() {
    suggestionsBox.innerHTML = matches.map((c, i) =>
      `<div class="suggestion-item${i === activeIdx ? ' active' : ''}" role="option" data-i="${i}">
         <img src="${esc(c.icon)}" alt="" loading="lazy"><span>${esc(c.name)}</span></div>`).join('');
    suggestionsBox.style.display = matches.length ? 'block' : 'none';
    const active = suggestionsBox.querySelector('.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  searchInput.addEventListener('input', () => {
    const q = normalizeText(searchInput.value);
    if (!q) return closeSuggestions();
    // primero los que empiezan por la búsqueda, luego los que la contienen
    const starts = [], contains = [];
    allChamps.forEach(c => {
      const n = normalizeText(c.name);
      if (n.startsWith(q)) starts.push(c); else if (n.includes(q)) contains.push(c);
    });
    matches = [...starts, ...contains].slice(0, 15);
    activeIdx = matches.length ? 0 : -1;
    paintSuggestions();
  });

  searchInput.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!matches.length) return;
      e.preventDefault();
      activeIdx = (activeIdx + (e.key === 'ArrowDown' ? 1 : -1) + matches.length) % matches.length;
      paintSuggestions();
    } else if (e.key === 'Enter' && matches[activeIdx]) {
      selectChampion(matches[activeIdx]);
    } else if (e.key === 'Escape') {
      closeSuggestions();
    }
  });

  suggestionsBox.addEventListener('click', e => {
    const item = e.target.closest('.suggestion-item');
    if (item) selectChampion(matches[+item.dataset.i]);
  });

  document.addEventListener('click', e => { if (!e.target.closest('.search-box')) closeSuggestions(); });

  function applyLangUi() {
    document.documentElement.lang = currentLang;
    langSelect.value = currentLang;
    if (!searchInput.disabled) searchInput.placeholder = T.searchPlaceholder;
    if (patchText) footer.textContent = `${T.footer} ${patchText} (CommunityDragon / Meraki)`;
  }

  async function loadList() {
    const list = await getJson(`/api/list?lang=${currentLang}`);
    allChamps = Object.values(list.data).sort((a, b) => a.name.localeCompare(b.name, currentLang));
    searchInput.disabled = false;
    applyLangUi();
  }

  langSelect.addEventListener('change', async () => {
    setLang(langSelect.value);
    try { localStorage.setItem('lang', currentLang); } catch (e) { /* sin almacenamiento */ }
    applyLangUi();
    try {
      await loadList();
      const same = currentChamp && allChamps.find(c => c.id === currentChamp.id);
      if (same) loadChampion(same);
    } catch (e) {
      showError(`${T.errList}: ${e.message}`);
    }
  });

  async function init() {
    try { setLang(localStorage.getItem('lang') || DEFAULT_LANG); } catch (e) { setLang(DEFAULT_LANG); }
    applyLangUi();
    getJson('/api/version')
      .then(v => { patchText = v.patch; applyLangUi(); })
      .catch(() => {});
    getJson('/api/icons').then(list => { availableIcons = new Set(list); }).catch(() => {});

    try {
      await loadList();
      const fromHash = decodeURIComponent(location.hash.slice(1));
      loadChampion(allChamps.find(c => c.id === fromHash) || allChamps.find(c => c.id === 'Aatrox') || allChamps[0]);
    } catch (e) {
      showError(`${T.errList}: ${e.message}`);
    }
  }

  init();
}

if (typeof module !== 'undefined') {
  module.exports = { attrLabel, publicPatch, setLang, parseInner, parseUnit, descChip, highlightDescription, formulaChip, classifyStat, classifyAttribute, formatValues, parseUnit, setIcons: s => { availableIcons = s; } };
}