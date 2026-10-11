// Site Search: tool-style view of one recorded run (runs/<id>.json). "Run search" replays the recorded run as a loading state.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const runId = (new URLSearchParams(location.search).get('run') || 'linker-mm3').replace(/[^a-z0-9-]/gi, '');
const DEC = { select: 'Select', conditional: 'Select w/ conditions', clarify: 'Clarify first', reject: "Don't select" };
const STEPS = [['rank', 'Ranking candidates', 6], ['contact', 'Verifying contacts', 1.5], ['quest', 'Questionnaires', 1.5], ['decide', 'Recommendations', 1]];
const isHuman = a => /^y/i.test(a.needs_human || '') || !a.answer;
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
const AKEY = 'sitesearch.' + runId + '.approved';

let RUN = null, ROWS = [], PROJ = null, US = null;
const S = { t: -1, sort: 'rank', dir: 1, sel: null, tab: 'evidence', checked: new Set(), approved: store.get(AKEY, {}), backtest: false, filter: '', miss: '', phase: 0, phaseUser: false };

fetch('runs/' + runId + '.json').then(r => { if (!r.ok) throw new Error('No run file: runs/' + runId + '.json'); return r.json(); })
  .then(run => { RUN = run; init(); })
  .catch(e => { $('#list').innerHTML = '<div class="empty">' + esc(e.message) + '</div>'; });

function init() {
  const d1 = RUN.stage1, d3 = RUN.stage3 || {}, cs = (RUN.stage2 || {}).contacts || [], ds = (RUN.stage4 || {}).decisions || [];
  const q16 = (d3.questionnaire || []).length;
  const mk = (key, base) => {
    const ans = (d3.answers || {})[key], qs = ans ? ans.filter(a => /^Q\d+$/.test(a.q_id)) : null;
    return { ...base, key, contact: cs.find(c => String(c.rank) === key), answers: ans, nAns: qs ? qs.filter(a => !isHuman(a)).length : null, nQ: q16, prefill: (d3.prefill || {})[key] || [], dec: ds.find(x => x.site_key === key) };
  };
  ROWS = d1.sites.map(s => mk(String(s.rank), { rank: s.rank, name: s.facility, city: s.city, state: s.state, score: s.score, reason: s.reason, past: s.past_trials || [], real: s.real, lat: s.lat, lon: s.lon }));
  (d3.sites || []).filter(s => s.kind === 'synthetic').forEach(s => {          // network sites the ranking never saw (e.g. Riverside)
    const dec = ds.find(x => x.site_key === s.key), m = /\(([^,]+),\s*([A-Z]{2})\)/.exec(dec ? dec.site : '');
    ROWS.unshift(mk(s.key, { rank: null, net: true, name: s.name, city: m ? m[1] : '', state: m ? m[2] : '', score: null, reason: 'Added from your site network (not ranked from public data).', past: [] }));
  });
  $('#qtag').textContent = RUN.trial.name + ' · ' + RUN.trial.sponsor + ' · ' + RUN.trial.drug;
  $('#run').onclick = run;
  $('#q').onkeydown = e => { if (e.key === 'Enter') run(); };
  $('#filter').oninput = e => { S.filter = e.target.value.toLowerCase(); draw(); };
  $('#backtest').onchange = e => { S.backtest = e.target.checked; draw(); };
  $('#bulk').onclick = () => { S.checked.forEach(k => { const r = ROWS.find(x => x.key === k); if (r && r.dec && done(3)) S.approved[k] = true; }); S.checked.clear(); store.set(AKEY, S.approved); draw(); };
  $('#csv').onclick = csv;
  document.addEventListener('click', onClick);
  if (new URLSearchParams(location.search).get('t') === 'end') S.t = 99;   // ?t=end skips the replay
  draw(); requestAnimationFrame(loop);
}

// ---- replay clock: S.t seconds into the recorded run; -1 = not run yet
const stepEnd = i => STEPS.slice(0, i + 1).reduce((a, s) => a + s[2], 0);
const prog = i => S.t < 0 ? 0 : Math.max(0, Math.min(1, (S.t - (stepEnd(i) - STEPS[i][2])) / STEPS[i][2]));
const done = i => prog(i) >= 1;
let last = 0, lastKey = '';
function loop(now) {
  const dt = Math.min(.2, (now - last) / 1000); last = now;
  if (S.t >= 0 && S.t < stepEnd(STEPS.length - 1)) S.t += dt;
  const key = vis().join('|');
  if (key !== lastKey) { lastKey = key; draw(); }
  requestAnimationFrame(loop);
}
function run() {
  const q = $('#q').value.trim().toLowerCase(), t = RUN.trial;
  S.miss = q && ![t.nct, t.name, t.drug, t.sponsor].some(x => (x || '').toLowerCase().includes(q)) ? $('#q').value.trim() : '';
  S.t = S.miss ? -1 : 0; S.sel = null; S.phase = 0; S.phaseUser = false; draw();
}
// how much of each step is visible right now
const dotsShown = () => Math.round(Math.min(1, prog(0) / .35) * (RUN.stage1.scored || []).length);
function vis() {
  const nr = Math.round(Math.max(0, (prog(0) - .35) / .65) * ROWS.length), nc = Math.round(prog(1) * 99), nq = Math.round(prog(2) * 99), nd = Math.round(prog(3) * 99);
  return [S.t < 0 ? -1 : nr, nc, nq, nd, dotsShown()];
}
const shown = () => { const [nr, nc, nq, nd] = vis(); const net = ROWS.filter(r => r.net), ranked = ROWS.filter(r => !r.net);
  return { rows: nr < 0 ? [] : ranked.slice(0, nr).concat(done(1) ? net : []), c: nc / 99, q: nq / 99, d: nd / 99 }; };
// a cell's data only appears once its step has reached that row
const has = (r, step, frac) => { const pool = ROWS.filter(x => step === 'contact' ? x.contact : step === 'quest' ? x.answers : x.dec); const i = pool.indexOf(r); return i >= 0 && i < Math.round(frac * pool.length); };

const PHASES = ['Ranking', 'Contacts', 'Questionnaires', 'Recommendations'], SIDE = ['evidence', 'contact', 'quest', 'decision'];
// while the run plays, the phase tabs follow the step that's running unless the user picked one
const curPhase = () => { const i = STEPS.findIndex((s, j) => !done(j)); return i < 0 ? STEPS.length - 1 : i; };

function draw() {
  const sh = shown();
  if (S.t >= 0 && !S.phaseUser) S.phase = curPhase();
  drawPhases(sh);
  const match = r => !S.filter || [r.name, r.city, r.state, r.contact && r.contact.pi].join(' ').toLowerCase().includes(S.filter);
  const val = r => S.sort === 'name' ? r.name : S.sort === 'state' ? r.state + r.city : S.sort === 'score' ? -(r.score ?? 9) : (r.rank ?? -1);
  const sorted = rows => rows.filter(match).sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * S.dir);
  const ranked = sh.rows.filter(r => !r.net);
  if (S.t < 0) $('#list').innerHTML = '<div class="empty">' + (S.miss ? 'No recorded run for “' + esc(S.miss) + '”. Try ' + esc(RUN.trial.nct) + '.' : 'Enter a trial (NCT ID, name, drug or sponsor) and run the search.') + '</div>';
  else drawTable(sorted(phaseRows(S.phase, sh)), sh);
  drawMap($('#map'), S.t < 0 ? [] : sorted(ranked));
  $('#selinfo').textContent = S.checked.size + ' selected';
  $('#bulkbar').hidden = S.phase !== 3;
  $('#bulk').disabled = !S.checked.size || !done(3);
  drawSide(sh);
}
function phaseRows(i, sh) {
  const step = ['rank', 'contact', 'quest', 'decide'][i], frac = [1, sh.c, sh.q, sh.d][i];
  return i === 0 ? sh.rows.filter(r => !r.net) : ROWS.filter(r => has(r, step, frac));
}
function drawPhases(sh) {
  const n = [sh.rows.filter(r => !r.net).length, phaseRows(1, sh).length, phaseRows(2, sh).length, phaseRows(3, sh).length];
  const meta = [n[0] ? 'top ' + n[0] + ' of ' + (RUN.stage1.n_candidates || '') : '', n[1] + ' sites · ' + phaseRows(1, sh).filter(r => r.contact.route !== 'office').length + ' doctor-first · ' + phaseRows(1, sh).filter(r => r.contact.route === 'office').length + ' office-first', phaseRows(2, sh).filter(r => r.nAns).length + '/' + n[2] + ' returned', ROWS.filter(r => r.dec && S.approved[r.key]).length + '/' + n[3] + ' approved'];
  $('#phases').innerHTML = PHASES.map((l, i) => { const p = S.t < 0 ? 0 : prog(i), st = p >= 1 ? 'ok' : p > 0 ? 'run' : '';
    return '<button data-phase="' + i + '" class="' + (S.phase === i ? 'on ' : '') + st + '"' + (S.t < 0 || (!p && i) ? ' disabled' : '') + '><i></i>' + l + (p > 0 ? ' <span class="cnt">' + esc(meta[i]) + '</span>' : '') + '</button>'; }).join('') +
    (S.backtest && S.t >= 0 && done(0) ? '<span class="grow"></span><span class="sub" style="align-self:center">Backtest: <b style="color:var(--ink)">' + RUN.stage1.score.found + ' of ' + RUN.stage1.score.of + '</b> actual sites in top 50 · baseline ' + ((RUN.stage1.score.baselines || {}).most_past_trials ?? '–') + '</span>' : '');
}

function drawTable(rows, sh) {
  const th = (k, l, right) => '<th' + (k ? ' data-sort="' + k + '"' : ' class="nosort"') + (right ? ' style="text-align:right"' : '') + '>' + l + (S.sort === k ? ' <span class="ar">' + (S.dir > 0 ? '↑' : '↓') + '</span>' : '') + '</th>';
  const plain = l => '<th class="nosort">' + l + '</th>', dash = '<span class="sub">—</span>';
  const site = r => '<td class="num">' + (r.rank ?? '') + '</td><td><div class="site">' + esc(r.name) + '</div>' + (r.net ? '<span class="badge b-net">Your network</span>' : '') + '</td>';
  const P = S.phase, chk = P === 3;
  const cols = [
    [th('state', 'Location'), th('score', 'Fit', 1), plain('Basis')].concat(S.backtest ? [plain('Actual')] : []),
    [plain('Contact first'), plain('<span title="Still there · Same drug · Same kind of trial · Has room">Criteria</span>'), '<th class="nosort" style="text-align:right" title="Competing recruiting trials they lead">Room</th>', '<th class="nosort" style="text-align:right">Conf</th>', plain('Heads-up'), plain('Research office')],
    [plain('Answered'), plain('Needs a human'), plain('Notes'), plain('Source')],
    [plain('Recommendation'), plain('Follow-up'), plain('Status')]][P];
  const cells = r => {
    if (P === 0) return '<td class="sub">' + esc([r.city, r.state].filter(Boolean).join(', ')) + '</td><td class="num">' + (r.score != null ? Math.round(r.score * 100) + '%' : '') + '</td><td class="sub basis" title="' + esc(r.reason) + '">' + esc(r.reason) + '</td>' + (S.backtest ? '<td>' + (r.real ? '<span class="b-ok">✓</span>' : '') + '</td>' : '');
    if (P === 1) { const c = r.contact, off = c.route === 'office', room = (c.criteria || {}).has_room || {};
      return '<td>' + (off ? '<span style="color:var(--ink);font-weight:500">Research office</span> <span class="badge b-conditional">office first</span>' : '<span style="color:var(--ink)">' + esc(c.pi) + '</span>') + '</td>' +
        '<td>' + critDots(c) + '</td>' +
        '<td class="num">' + (room.competing ?? '') + '</td><td class="num">' + Math.round((c.confidence || 0) * 100) + '%</td>' +
        '<td class="sub hu" title="' + esc(c.note || '') + '">' + esc(headsUp(c.note)) + '</td>' +
        '<td>' + (c.contact_url ? '<a href="' + esc(c.contact_url) + '" target="_blank" rel="noopener noreferrer" class="mono dom" title="' + esc(c.contact_domain || '') + '"' + (off ? ' style="font-weight:600"' : '') + '>' + esc(c.contact_domain || 'link') + ' ↗</a>' : dash) + '</td>'; }
    if (P === 2) { const notes = r.answers.filter(a => a.q_id === 'NOTE').length;
      return '<td class="mono">' + (r.nAns ? r.nAns + '/' + r.nQ : '<span class="sub">awaiting</span>') + '</td><td class="mono">' + (r.nAns ? r.nQ - r.nAns : dash) + '</td><td class="mono">' + (notes || dash) + '</td><td class="sub">' + (r.net ? 'site files' : 'public records') + '</td>'; }
    const ap = !!S.approved[r.key];
    return '<td><span class="badge b-' + esc(r.dec.decision) + '">' + esc(DEC[r.dec.decision] || r.dec.decision) + '</span></td><td class="mono">' + (r.dec.follow_ups || []).length + ' Qs</td>' +
      '<td>' + (ap ? '<span class="b-ok">✓ Approved</span>' : '<button class="btn sm" data-approve="' + esc(r.key) + '">Approve</button>') + '</td>';
  };
  const wait = !rows.length ? (prog(P) > 0 ? PHASES[P] + ' running…' : S.t >= 0 && P === 0 ? 'Scanning ' + (RUN.stage1.n_candidates || '') + ' candidates…' : 'No sites match.') : '';
  $('#list').innerHTML = '<table><thead><tr>' + (chk ? '<th class="nosort" style="width:28px"><input type="checkbox" data-all></th>' : '') + th('rank', '#', 1) + th('name', 'Site') + cols.join('') + '</tr></thead><tbody>' +
    rows.map(r => '<tr data-row="' + esc(r.key) + '" class="' + (S.sel === r.key ? 'sel' : '') + '">' + (chk ? '<td><input type="checkbox" data-check="' + esc(r.key) + '"' + (S.checked.has(r.key) ? ' checked' : '') + '></td>' : '') + site(r) + cells(r) + '</tr>').join('') +
    '</tbody></table>' + (wait ? '<div class="empty">' + wait + '</div>' : '');
}

const fitColor = fit => { const S0 = [[190, 222, 247], [122, 160, 194], [47, 59, 74]], f = Math.max(0, Math.min(1, (0.97 - fit) / 0.92)); const [p, q, k] = f < .5 ? [S0[0], S0[1], f * 2] : [S0[1], S0[2], (f - .5) * 2]; return 'rgb(' + p.map((v, i) => Math.round(v + (q[i] - v) * k)).join(',') + ')'; };
// Draw the US map into el once; dots (all scored candidates) and pins (top 50) are refreshed on every call.
function drawMap(el, rows) {
  if (!el.querySelector('.mapwrap')) {
    el.innerHTML = '<div class="mapwrap"><svg viewBox="0 0 975 610"></svg><div class="dots"></div><div class="pins"></div></div>';
    el._h = null;
    if (window.d3 && window.topojson) {
      PROJ = PROJ || d3.geoAlbersUsa().scale(1300).translate([487.5, 305]);
      const svg = el.querySelector('svg'), paint = us => { const path = d3.geoPath(PROJ), g = d3.select(svg);
        g.append('path').attr('d', path(topojson.feature(us, us.objects.nation))).attr('fill', '#F1F0EC');
        g.append('path').attr('d', path(topojson.mesh(us, us.objects.states, (a, b) => a !== b))).attr('fill', 'none').attr('stroke', '#DDDCD8').attr('stroke-width', .8); };
      US ? paint(US) : fetch('vendor/states-10m.json').then(r => r.json()).then(us => { US = us; paint(us); });
    }
  }
  if (!PROJ) return;
  const at = (lat, lon) => { const p = lat != null && PROJ([lon, lat]); return p ? [p[0] / 9.75, p[1] / 6.1] : null; };
  {   // every scored candidate appears first, then they fade as the top 50 get pinned
    const nd = S.t < 0 ? 0 : dotsShown(), faded = shown().rows.length > 0;
    sync(el.querySelector('.dots'), (RUN.stage1.scored || []).slice(0, nd).map(s => { const p = at(s.lat, s.lon); return p ? '<div class="mdot" style="left:' + p[0] + '%;top:' + p[1] + '%;background:' + fitColor(s.score) + ';opacity:' + (faded ? .3 : .9) + '"></div>' : ''; }).filter(Boolean));
  }
  const seen = {};
  sync(el.querySelector('.pins'), rows.filter(r => r.lat != null).sort((a, b) => a.rank - b.rank).map(r => {
    const p = at(r.lat, r.lon); if (!p) return '';
    const k = p.map(Math.round).join(','), n = seen[k] = (seen[k] || 0) + 1, rr = n > 1 ? 12 : 0, a = n * 2.1;   // same-city sites share a point: fan them out
    const big = r.rank <= 12, sz = big ? 14 : 8;
    return '<div class="pin' + (S.sel === r.key ? ' sel' : '') + (S.backtest && r.real ? ' real' : '') + '" data-row="' + esc(r.key) + '" title="#' + r.rank + ' ' + esc(r.name) + '" style="left:calc(' + p[0] + '% + ' + Math.round(rr * Math.cos(a)) + 'px);top:calc(' + p[1] + '% + ' + Math.round(rr * Math.sin(a)) + 'px);width:' + sz + 'px;height:' + sz + 'px;background:' + fitColor(r.score) + ';z-index:' + (60 - r.rank) + '">' + (big ? r.rank : '') + '</div>';
  }).filter(Boolean));
}
// Replace only the children whose HTML changed, so unchanged pins keep their DOM node and don't replay the drop-in animation.
function sync(el, items) {
  const prev = el._h && el.children.length === el._h.length ? el._h : (el.innerHTML = '', []);
  items.forEach((h, i) => {
    if (prev[i] === h) return;
    const t = document.createElement('template'); t.innerHTML = h;
    el.children[i] ? el.children[i].replaceWith(t.content) : el.appendChild(t.content);
  });
  while (el.children.length > items.length) el.lastElementChild.remove();
  el._h = items;
}

function drawSide(sh) {
  const r = ROWS.find(x => x.key === S.sel);
  if (!r) { $('#detail').innerHTML = '<div class="empty">' + (S.t < 0 ? '' : 'Select a site to see details.') + '</div>'; return; }
  const ok = { evidence: true, contact: has(r, 'contact', sh.c), quest: has(r, 'quest', sh.q), decision: has(r, 'decide', sh.d) };
  if (!ok[S.tab]) S.tab = 'evidence';
  const tab = (k, l) => '<button data-tab="' + k + '" class="' + (S.tab === k ? 'on' : '') + '"' + (ok[k] ? '' : ' disabled') + '>' + l + '</button>';
  $('#detail').innerHTML = '<div class="dh"><div class="t">' + esc(r.name) + '</div><div class="sub">' + esc([r.city, r.state].filter(Boolean).join(', ')) + (r.rank ? ' · rank ' + r.rank + ' · fit ' + r.score.toFixed(2) : ' · your network') + '</div>' +
    '<div class="tabs">' + tab('evidence', 'Evidence') + tab('contact', 'Contact') + tab('quest', 'Questionnaire') + tab('decision', 'Recommendation') + '</div></div>' +
    '<div class="db">' + ({ evidence: sideEvidence, contact: sideContact, quest: sideQuest, decision: sideDecision }[S.tab])(r) + '</div>';
}
function sideEvidence(r) {
  return '<div>' + esc(r.reason) + '</div>' + (S.backtest && r.real ? '<div class="flag" style="background:var(--green);color:var(--greenInk)">Backtest: this site actually ran ' + esc(RUN.trial.name) + '.</div>' : '') +
    (r.past.length ? '<div class="lbl">Past trials</div>' + r.past.map(t => '<div class="item"><span>' + esc(t.title || t.nct) + '</span><span class="mono sub">' + esc([t.nct, t.sponsor, (t.start || '').slice(0, 10)].filter(Boolean).join(' · ')) + '</span></div>').join('') : '') +
    (r.prefill.length ? '<div class="lbl">Known from public records</div>' + r.prefill.map(f => '<div class="item"><span class="sub">' + esc(f.fact) + '</span><span>' + esc(f.value) + '</span><span><span class="src">' + esc(f.source_type || '') + '</span></span></div>').join('') : '');
}
const CRIT = [['still_there', 'Still there'], ['same_drug', 'Same drug or class'], ['same_kind', 'Same kind of trial'], ['has_room', 'Has room']];
const metOf = c => k => (((c.criteria || {})[k] || {}).met || 'unknown');
// 4 dots in methodology order: filled = yes, hollow = no, grey = unknown
const critDots = c => '<span class="dots4">' + CRIT.map(([k, l]) => { const m = metOf(c)(k), f = ((c.criteria || {})[k] || {}).finding || '';
  return '<i class="' + m + '" title="' + esc(l + ': ' + m + (f ? ' · ' + f : '')) + '"></i>'; }).join('') + '</span>';
const headsUp = n => { if (!n) return ''; const w = n.split(/\s+/); return w.slice(0, 7).join(' ') + (w.length > 7 ? '…' : ''); };
function sideContact(r) {
  const c = r.contact, off = c.route === 'office', cr = c.criteria || {}, met = metOf(c);
  const why = off ? 'Office first: the pick rests on seniority only, so let the site name the investigator.'
    : 'Doctor first: ' + (met('same_drug') === 'yes' ? 'has led this drug or class at this site.' : 'has led the same kind of trial at this site.');
  const mark = m => m === 'yes' ? '<span class="b-ok">✓ yes</span>' : m === 'no' ? '<span class="b-warn">✗ no</span>' : '<span class="sub">? unknown</span>';
  const room = cr.has_room || {};
  return '<div class="flag" style="' + (off ? '' : 'background:var(--green);color:var(--greenInk)') + '">' + why + '</div>' +
    '<div class="lbl">Doctor</div><div class="kv"><div>' + (off ? 'Suggested' : 'Contact') + '</div><div style="color:var(--ink);font-weight:500">' + esc(c.pi) + '</div>' +
    (c.alts && c.alts.length ? '<div>Backups</div><div>' + esc(c.alts.join(', ')) + '</div>' : '') +
    '<div>Confidence</div><div class="mono">' + Math.round((c.confidence || 0) * 100) + '%</div></div><div>' + esc(c.evidence) + '</div>' +
    '<div class="lbl">Criteria</div>' + CRIT.map(([k, l], i) => { const x = cr[k] || {};
      return '<div class="item"><span><span class="mono sub">' + (i + 1) + '</span> ' + l + ' · ' + mark(x.met) + (x.source ? ' <span class="src">' + esc(x.source) + '</span>' : '') + '</span><span class="sub">' + esc(x.finding || '') +
        (k === 'has_room' && room.competing != null ? ' · agent ' + room.competing + (c.competing_rule != null ? ', script ' + c.competing_rule : '') : '') + '</span></div>'; }).join('') +
    (c.note ? '<div class="lbl">Note</div><div class="flag">' + esc(c.note) + '</div>' : '') +
    '<div class="lbl">Research office</div>' + (c.contact_url ? '<div class="kv"><div>Page</div><div><a href="' + esc(c.contact_url) + '" target="_blank" rel="noopener noreferrer">' + esc(c.contact_domain || c.contact_url) + ' ↗</a></div><div>Loads</div><div class="' + (c.url_status && c.url_status < 400 || c.url_status === 403 ? 'b-ok' : 'b-warn') + '">' + (c.url_status ? (c.url_status === 403 ? '✓ (403, bot-blocked)' : c.url_status < 400 ? '✓ ' + c.url_status : '✗ ' + c.url_status) : 'not checked') + '</div></div>' : '<div class="sub">None found</div>') +
    '<div class="sub">No emails or phone numbers. A person sends.</div>';
}
function sideQuest(r) {
  const qs = RUN.stage3.questionnaire, notes = r.answers.filter(a => a.q_id === 'NOTE');
  return '<div class="sub">' + r.nAns + ' of ' + r.nQ + ' answered' + (r.net ? ' from site files' : ' from public records') + ' · ' + (r.nQ - r.nAns) + ' need a human</div>' +
    qs.map(q => { const a = r.answers.find(x => x.q_id === q.id) || {}, h = isHuman(a);
      return '<div class="q' + (h ? ' h' : '') + '"><div class="sub"><span class="mono">' + esc(q.id) + '</span> ' + esc(q.question) + '</div>' +
        (h ? '<div class="b-warn" style="font-size:12px">Needs a human' + (a.note ? ': ' + esc(a.note) : '') + '</div>' : '<div style="color:var(--ink);font-weight:500">' + esc(a.answer) + '</div>' + (a.note ? '<div class="sub">' + esc(a.note) + '</div>' : '')) +
        (a.source ? '<div>' + a.source.split(';').map(s => '<span class="src">' + esc(s.trim()) + '</span>').join('') + '</div>' : '') + '</div>'; }).join('') +
    (notes.length ? '<div class="lbl">Notes</div>' + notes.map(a => '<div class="item"><span>' + esc(a.answer) + '</span>' + (a.source ? '<span>' + a.source.split(';').map(s => '<span class="src">' + esc(s.trim()) + '</span>').join('') + '</span>' : '') + '</div>').join('') : '');
}
function sideDecision(r) {
  const d = r.dec, ap = !!S.approved[r.key];
  return '<div><span class="badge b-' + esc(d.decision) + '">' + esc(DEC[d.decision] || d.decision) + '</span></div>' +
    '<div class="lbl">Reasons</div>' + (d.reasons || []).map(x => '<div class="item"><span>' + esc(x) + '</span></div>').join('') +
    ((d.follow_ups || []).length ? '<div class="lbl">Draft follow-up (' + d.follow_ups.length + ')</div><div class="q">' + d.follow_ups.map(f => '<div>' + esc(f) + '</div>').join('') + '</div>' : '') +
    '<div style="display:flex;gap:8px;align-items:center">' + (ap ? '<span class="b-ok">✓ Approved to send</span><button class="btn" data-undo="' + esc(r.key) + '">Undo</button>' : '<button class="btn primary" data-approve="' + esc(r.key) + '">Approve &amp; send</button><span class="sub">Nothing is sent until approved.</span>') + '</div>';
}

function onClick(e) {
  const t = e.target;
  if (t.matches('[data-check]')) { t.checked ? S.checked.add(t.dataset.check) : S.checked.delete(t.dataset.check); draw(); return; }
  if (t.matches('[data-all]')) { document.querySelectorAll('[data-check]').forEach(x => t.checked ? S.checked.add(x.dataset.check) : S.checked.delete(x.dataset.check)); draw(); return; }
  const el = t.closest('[data-sort],[data-row],[data-tab],[data-approve],[data-undo],[data-phase]'); if (!el) return;
  if (el.dataset.phase != null) { S.phase = +el.dataset.phase; S.phaseUser = true; S.tab = SIDE[S.phase]; S.checked.clear(); draw(); return; }
  if (el.dataset.sort) { S.dir = S.sort === el.dataset.sort ? -S.dir : 1; S.sort = el.dataset.sort; }
  else if (el.dataset.row) S.sel = el.dataset.row;
  else if (el.dataset.tab) S.tab = el.dataset.tab;
  else if (el.dataset.approve) { S.approved[el.dataset.approve] = true; store.set(AKEY, S.approved); }
  else if (el.dataset.undo) { delete S.approved[el.dataset.undo]; store.set(AKEY, S.approved); }
  draw();
}

function csv() {
  const q = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
  const lines = [['rank', 'site', 'city', 'state', 'fit', 'pi', 'pi_active', 'answered', 'recommendation', 'approved'].join(',')].concat(shown().rows.map(r =>
    [r.rank, r.name, r.city, r.state, r.score, r.contact && r.contact.pi, r.contact && r.contact.bmis_active, r.nAns != null ? r.nAns + '/' + r.nQ : '', r.dec && r.dec.decision, !!S.approved[r.key]].map(q).join(',')));
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/csv' })); a.download = RUN.trial.name + '-sites.csv'; a.click();
}
