// Pruebas de la lógica pura de app.js (sin navegador). Ejecutar con:  node --test tests/js
const test = require('node:test');
const assert = require('node:assert');
const app = require('../../app.js');

test.beforeEach(() => { app.setLang('en'); app.setIcons(new Set(['ad', 'hp', 'ap', 'onhit'])); });

test('classifyStat distingue vida de curación y respeta el orden de reglas', () => {
  assert.strictEqual(app.classifyStat('bonus health'), 'hp');
  assert.strictEqual(app.classifyStat('healing'), 'heal');
  assert.strictEqual(app.classifyStat('armor penetration'), 'lethality');
  assert.strictEqual(app.classifyStat('magic resistance'), 'mr');
  assert.strictEqual(app.classifyStat('palabra cualquiera'), null);
});

test('classifyAttribute usa el tipo de daño de la habilidad cuando el nombre es genérico', () => {
  assert.strictEqual(app.classifyAttribute('Physical Damage'), 'phys');
  assert.strictEqual(app.classifyAttribute('Damage', 'MAGIC_DAMAGE'), 'magic');
  assert.strictEqual(app.classifyAttribute('Damage', ''), 'base');
  assert.strictEqual(app.classifyAttribute('Bonus Attack Damage'), 'ad');
});

test('formatValues: iguales, listas y rangos por nivel', () => {
  assert.deepStrictEqual(app.formatValues([5, 5, 5]), { text: '5', levels: 0 });
  assert.deepStrictEqual(app.formatValues([10, 20, 30]), { text: '10 / 20 / 30', levels: 0 });
  const lv = app.formatValues(Array.from({ length: 18 }, (_, i) => 22 - i));
  assert.deepStrictEqual(lv, { text: '22–5', levels: 18 });
  assert.strictEqual(app.formatValues([1.23456]).text, '1.23');
});

test('parseUnit: vida del objetivo, propia y escalados "por cada 100"', () => {
  const target = app.parseUnit("% of target's maximum health", true);
  assert.deepStrictEqual([target.type, target.scope, target.owner], ['hp', 'max', 'target']);
  const own = app.parseUnit('% bonus health', true);
  assert.deepStrictEqual([own.type, own.scope, own.owner], ['hp', 'bonus', 'self']);
  const per = app.parseUnit('% AP per 100 bonus health');
  assert.strictEqual(per.type, 'ap');
  assert.deepStrictEqual([per.per.n, per.per.type, per.per.scope], ['100', 'hp', 'bonus']);
});

test('parseUnit extrae el escalado entre paréntesis', () => {
  const u = app.parseUnit("% (+ 7% per 100 AP) of the target's maximum health", true);
  assert.strictEqual(u.type, 'hp');
  assert.strictEqual(u.inner.length, 1);
  assert.deepStrictEqual([u.inner[0].value, u.inner[0].per.n, u.inner[0].type], ['7', '100', 'ap']);
});

test('formulaChip: daño mágico al objetivo va en celeste y sin icono de vida propia', () => {
  const html = app.formulaChip({ values: [15], units: ["% of target's maximum health"] }, 1, 'Magic Damage');
  assert.match(html, /stat-chip magic/);
  assert.doesNotMatch(html, /hp\.png/);
  assert.match(html, /target's/);
});

test('formulaChip: escalado con estadística propia lleva su icono', () => {
  const html = app.formulaChip({ values: [60, 70], units: ['% bonus AD'] }, 1, 'Physical Damage');
  assert.match(html, /^\(\+ <span class="stat-chip ad scope-bonus"><img src="\/icons\/ad\.png"/);
  assert.match(html, /60 \/ 70%/);
});

test('renderRich convierte marcas del servidor en HTML', () => {
  const html = app.renderRich('{{t:phys}}10 (+ {{S|ad|bonus|60}}){{/t}} y {{L|4|10}}% <script>');
  assert.match(html, /<span class="phys">/);
  assert.match(html, /stat-chip ad scope-bonus/);
  assert.match(html, /4–10% <span class="lvl-tag">\(lvl 1-18\)<\/span>/);
  assert.match(html, /&lt;script&gt;/);                      // el texto se escapa
});

test('renderRich pinta icono delante de on-hit', () => {
  assert.match(app.renderRich('{{t:onhit}}on-hit{{/t}}'), /<img src="\/icons\/onhit\.png"/);
});

test('highlightDescription: tipo de daño, control de masas y vida del objetivo', () => {
  const html = app.highlightDescription("Deals 100 (+15% of the target's maximum health) magic damage and stuns.");
  assert.match(html, /<strong class="magic">magic damage<\/strong>/);
  assert.match(html, /<span class="cc">stuns<\/span>/);
  assert.match(html, /stat-chip magic[^"]*owner-target/);
});

test('publicPatch solo quita la V', () => {
  assert.strictEqual(app.publicPatch('V25.05'), '25.05');
});
