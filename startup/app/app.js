// Sponsorside: tool-style view of one recorded run (runs/<id>.json). "Run search" replays the recorded run as a loading state.
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const runId = (new URLSearchParams(location.search).get('run') || 'linker-mm3').replace(/[^a-z0-9-]/gi, '');
const DEC = { select: 'Select', conditional: 'Select w/ conditions', clarify: 'Clarify first', reject: "Don't select" };
const STEPS = [['rank', 'Ranking candidates', 7], ['contact', 'Verifying contacts', 5], ['quest', 'Questionnaires', 5], ['decide', 'Recommendations', 3]];   // base seconds; each run varies
const isHuman = a => /^y/i.test(a.needs_human || '') || !a.answer;
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
const AKEY = 'sitesearch.' + runId + '.approved', SKEY = 'sitesearch.' + runId + '.sent';

let RUN = null, ROWS = [], PROJ = null, US = null;
const S = { t: -1, sort: 'rank', dir: 1, sel: null, tab: 'evidence', checked: new Set(), approved: store.get(AKEY, {}), sent: store.get(SKEY, {}), backtest: false, filter: '', miss: '', phase: 0, phaseUser: false, p: [0, 0, 0, 0], active: -1 };

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
  $('#run').onclick = () => run($('#q').value);
  $('#q').onkeydown = e => { if (e.key === 'Enter') run($('#q').value); };
  $('#run0').onclick = () => run($('#q0').value);
  $('#q0').onkeydown = e => { if (e.key === 'Enter') run($('#q0').value); };
  initDrop();
  initClientDrop();
  $('#shell .logo').ondblclick = () => openClient((RUN.stage3.sites.find(x => x.kind === 'synthetic') || RUN.stage3.sites[0]).key);   // secret: double-click logo to swap sides
  $('#client .logo').ondblclick = closeClient;
  setTimeout(() => $('#q0').focus(), 0);
  $('#filter').oninput = e => { S.filter = e.target.value.toLowerCase(); draw(); };
  $('#backtest').onchange = e => { S.backtest = e.target.checked; draw(); };
  $('#bulk').onclick = () => { S.checked.forEach(k => { const r = ROWS.find(x => x.key === k); if (r && r.dec && done(3)) S.approved[k] = true; }); S.checked.clear(); store.set(AKEY, S.approved); draw(); };
  $('#csv').onclick = csv;
  document.addEventListener('click', onClick);
  document.addEventListener('keydown', onKey);
  if (new URLSearchParams(location.search).get('t') === 'end') { S.t = 0; S.p = STEPS.map(() => 1); $('#q').value = RUN.trial.nct; $('#shell').classList.remove('idle'); }   // ?t=end skips the replay
  draw(); requestAnimationFrame(loop);
}

// ---- start screen: the search box doubles as a drop zone for a protocol folder (listed only, not parsed yet)
let DROPPED = [];
function initDrop() {
  const box = $('#drop'), show = names => { DROPPED = names; $('#files').innerHTML = names.slice(0, 200).map(n => '<li title="' + esc(n) + '">' + esc(n) + '</li>').join('') + (names.length > 200 ? '<li>… ' + (names.length - 200) + ' more</li>' : '');
    $('#dz').textContent = names.length ? names.length + ' file' + (names.length > 1 ? 's' : '') + ' added' : ''; $('#startmsg').textContent = ''; };
  ['dragenter', 'dragover'].forEach(ev => box.addEventListener(ev, e => { e.preventDefault(); box.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => box.addEventListener(ev, e => { e.preventDefault(); if (ev === 'drop' || !box.contains(e.relatedTarget)) box.classList.remove('over'); }));
  box.addEventListener('drop', async e => {
    const entries = [...e.dataTransfer.items].map(i => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
    show(entries.length ? (await Promise.all(entries.map(walk))).flat() : [...e.dataTransfer.files].map(f => f.name));
  });
  $('#browse').onclick = e => { e.preventDefault(); $('#picker').click(); };
  $('#picker').onchange = e => show([...e.target.files].map(f => f.webkitRelativePath || f.name));
}
// list every file path under a dropped folder
function walk(entry) {
  if (entry.isFile) return Promise.resolve([entry.fullPath.replace(/^\//, '')]);
  const reader = entry.createReader(), all = [];
  return new Promise(res => { const next = () => reader.readEntries(async es => { if (!es.length) return res((await Promise.all(all.map(walk))).flat()); all.push(...es); next(); }, () => res([])); next(); });
}

// ---- replay clock. S.t: -1 = not run, 0 = run started. S.p[i]: progress of step i (0..1).
// Only one step runs at a time; when it finishes the run waits for Space to start the next one.
// Progress is deliberately uneven: speed drifts, and the step stalls now and then like a slow API call.
const prog = i => S.t < 0 ? 0 : S.p[i];
const done = i => prog(i) >= 1;
const rand = (a, b) => a + Math.random() * (b - a);
const SPEED = 1;   // sponsor-side replay speed; stalls and start lag below are scaled by it too
let last = 0, lastKey = '', J = null;   // J: the running step's jitter state
function startStep(i) {
  S.active = i; S.phaseUser = false;
  J = { dur: STEPS[i][2] * rand(.8, 1.5), speed: rand(.5, 1.5), stallUntil: performance.now() + rand(300, 900) / (2 * SPEED) };   // short "connecting" lag first
}
function tickStep(now, dt) {
  const i = S.active; if (i < 0) return;
  if (now < J.stallUntil) return;
  const smooth = i === 0;   // ranking: few, short hiccups so pins and rows flow in steadily
  if (Math.random() < dt * (smooth ? .15 : .7) * 2 * SPEED) { J.stallUntil = now + (smooth ? rand(100, 350) : rand(150, 1300)) / (2 * SPEED); return; }   // stalls/sec
  J.speed = Math.max(smooth ? .7 : .25, Math.min(smooth ? 1.4 : 2.2, J.speed + rand(-.6, .6) * dt * 3));   // speed random-walks
  S.p[i] = Math.min(1, S.p[i] + dt / J.dur * J.speed * 1.2 * SPEED);
  if (S.p[i] >= 1) S.active = -1;
}
function loop(now) {
  const dt = Math.min(.2, (now - last) / 1000); last = now;
  tickStep(now, dt);
  const pct = S.t < 0 ? 0 : Math.floor(S.p.reduce((a, b) => a + b, 0) / S.p.length * 100);
  $('#bar').style.width = pct + '%'; $('#bar').parentNode.classList.toggle('done', pct >= 100); $('#pct').textContent = pct + '%';
  const next = nextStep();
  $('#hint').textContent = S.t >= 0 && S.active < 0 && next >= 0 ? 'Space ▸ ' + PHASES[next] : '';
  const key = vis().join('|') + S.active;
  if (key !== lastKey) { lastKey = key; draw(); }
  requestAnimationFrame(loop);
}
const nextStep = () => S.p.findIndex(p => p < 1);
let typing = false;
function onKey(e) {
  if ($('#track').classList.contains('client-on')) { if (e.key === 'Escape') closeClient(); return; }
  // demo: on the start screen, Space types the demo trial ID; Space again runs it
  if (e.code === 'Space' && $('#shell').classList.contains('idle') && (e.target === $('#q0') || !e.target.matches('input, textarea, select'))) {
    const box = $('#q0'), id = RUN.trial.nct, v = box.value.trim();
    if (!v || typing) { e.preventDefault(); if (!typing) typeIn(box, id); return; }
    if (v === id) { e.preventDefault(); run(v); return; }
  }
  if (e.code !== 'Space' || e.target.matches('input, textarea, select')) return;
  e.preventDefault(); if (e.target.blur) e.target.blur();   // a focused button would otherwise "click" on Space
  if (S.t < 0) { run($('#q0').value); return; }
  const n = nextStep();
  if (S.active < 0 && n >= 0) startStep(n);
}
function typeIn(box, text) {
  typing = true; box.value = ''; box.focus(); $('#startmsg').textContent = '';
  let i = 0; const t = setInterval(() => { box.value = text.slice(0, ++i); if (i >= text.length) { clearInterval(t); typing = false; } }, (45 + Math.random() * 40) / 2);
}
function run(raw) {
  const q = (raw || '').trim(), ql = q.toLowerCase(), t = RUN.trial, idle = $('#shell').classList.contains('idle');
  const hit = q && [t.nct, t.name, t.drug, t.sponsor].some(x => (x || '').toLowerCase().includes(ql));
  if (idle && !hit) {   // stay on the start screen and say why
    $('#startmsg').textContent = !q ? (DROPPED.length ? 'Reading dropped files isn\'t connected yet. Enter the trial ID to run.' : 'Enter a trial ID to run.') : 'No recorded run for “' + q + '”. Try ' + t.nct + '.';
    return;
  }
  $('#shell').classList.remove('idle'); $('#q').value = q;
  S.miss = hit ? '' : q;
  S.t = S.miss ? -1 : 0; S.p = STEPS.map(() => 0); S.active = -1; S.sel = null; S.phase = 0; S.phaseUser = false;
  if (!S.miss) startStep(0);
  draw();
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
const curPhase = () => S.active >= 0 ? S.active : Math.max(0, S.p.map(p => p >= 1).lastIndexOf(true));

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
  const tip = (label, title, lines, st) => '<th class="nosort tipcell"' + (st ? ' style="' + st + '"' : '') + '>' + label + ' <span class="qm">?</span><div class="tip"><b>' + title + '</b>' + lines.map((l, i) => '<div><i class="n">' + (i + 1) + '</i><b>' + l[0] + '</b> ' + l[1] + '</div>').join('') + '</div></th>';
  const P = S.phase, chk = P === 3;
  const cols = [
    [th('state', 'Location'), th('score', 'Fit', 1).replace('<th', '<th class="tipcell"').replace('Fit', 'Fit <span class="qm">?</span>' + '<div class="tip"><b>Site fit, 0 to 1</b><div><i class="n">1</i><b>Same sponsor</b> ran this sponsor\'s earlier blood cancer or bispecific trials.</div><div><i class="n">2</i><b>CRS experience</b> ran BCMA, T-cell engager or CAR-T myeloma trials.</div><div><i class="n">3</i><b>Myeloma volume</b> industry myeloma trials since 2018.</div><div><i class="n">4</i><b>Phase 3</b> has run late-stage myeloma trials.</div></div>'), plain('Basis')].concat(S.backtest ? [plain('Actual')] : []),
    [plain('Contact first'), '<th class="nosort tipcell">Criteria <span class="qm">?</span><div class="tip"><b>Doctor criteria, in order</b><div><i class="n">1</i><b>Still there</b> filed an FDA 1572 at this site in the last 18 months. Fail = out.</div><div><i class="n">2</i><b>Same drug</b> led this drug or its class here before.</div><div><i class="n">3</i><b>Same kind</b> led trials in this disease, same phase or earlier, here.</div><div><i class="n">4</i><b>Has room</b> few competing recruiting trials they lead now.</div><div class="leg"><span class="dots4"><i class="yes"></i></span> yes <span class="dots4"><i class="no"></i></span> no <span class="dots4"><i class="unknown"></i></span> unknown</div></div></th>', '<th class="nosort" style="text-align:right" title="Competing recruiting trials they lead">Room</th>', tip('Conf', 'Confidence, 0 to 100%', [['Agent\'s own', 'how sure the agent is of the pick; no formula.'], ['Still there', 'the gate rechecks it in FDA BMIS itself.'], ['Room', 'the gate rechecks it against a script count.'], ['Not checked', 'the score itself; read it with the 4 criteria.']], 'text-align:right'), plain('Heads-up'), plain('Research office')],
    [plain('Answered'), tip('Needs a human', 'When the agent stops', [['No source', 'no site file answers it; it names who should.'], ['A decision', 'commitments like PI, enrollment or budget.'], ['Estimates', 'patient counts get a range, still flagged.'], ['Never guess', 'the answer stays blank.']]), plain('Notes'), plain('Source'), plain('Sent')],
    [tip('Recommendation', 'Decision per site', [['Select', 'meets everything known, nothing blocking.'], ['Conditional', 'selectable once fixable items are resolved.'], ['Clarify', 'key answers still open; can\'t judge yet.'], ['Reject', 'a requirement it can\'t meet.']]), plain('Follow-up'), plain('Status')]][P];
  const cells = r => {
    if (P === 0) return '<td class="sub">' + esc([r.city, r.state].filter(Boolean).join(', ')) + '</td><td class="num">' + (r.score != null ? Math.round(r.score * 100) + '%' : '') + '</td><td class="sub basis" title="' + esc(r.reason) + '">' + esc(r.reason) + '</td>' + (S.backtest ? '<td>' + (r.real ? '<span class="b-ok">✓</span>' : '') + '</td>' : '');
    if (P === 1) { const c = r.contact, off = c.route === 'office', room = (c.criteria || {}).has_room || {};
      return '<td>' + (off ? '<span style="color:var(--ink);font-weight:500">Research office</span> <span class="badge b-conditional">office first</span>' : '<span style="color:var(--ink)">' + esc(c.pi) + '</span>') + '</td>' +
        '<td>' + critDots(c) + '</td>' +
        '<td class="num">' + (room.competing ?? '') + '</td><td class="num">' + Math.round((c.confidence || 0) * 100) + '%</td>' +
        '<td class="sub hu" title="' + esc(c.note || '') + '">' + esc(headsUp(c.note)) + '</td>' +
        '<td>' + (c.contact_url ? '<a href="' + esc(c.contact_url) + '" target="_blank" rel="noopener noreferrer" class="mono dom" title="' + esc(c.contact_domain || '') + '"' + (off ? ' style="font-weight:600"' : '') + '>' + esc(c.contact_domain || 'link') + ' ↗</a>' : dash) + '</td>'; }
    if (P === 2) { const notes = r.answers.filter(a => a.q_id === 'NOTE').length;
      return '<td class="mono">' + (r.nAns ? r.nAns + '/' + r.nQ : '<span class="sub">awaiting</span>') + '</td><td class="mono">' + (r.nAns ? r.nQ - r.nAns : dash) + '</td><td class="mono">' + (notes || dash) + '</td><td class="sub">' + (r.net ? 'site files' : 'public records') + '</td>' + '<td>' + sentBtn(r.key) + (r.net ? ' <button class="btn sm" data-answer="' + esc(r.key) + '">Answer</button>' : '') + '</td>'; }
    const ap = !!S.approved[r.key];
    return '<td><span class="badge b-' + esc(r.dec.decision) + '">' + esc(DEC[r.dec.decision] || r.dec.decision) + '</span></td><td class="mono">' + (r.dec.follow_ups || []).length + ' Qs</td>' +
      '<td>' + (ap ? '<span class="b-ok">✓ Approved</span>' : '<button class="btn sm" data-approve="' + esc(r.key) + '">Approve</button>') + '</td>';
  };
  const wait = !rows.length ? (prog(P) > 0 ? PHASES[P] + ' running…' : S.t >= 0 && P === 0 ? 'Scanning ' + (RUN.stage1.n_candidates || '') + ' candidates…' : 'No sites match.') : '';
  const head = '<tr>' + (chk ? '<th class="nosort" style="width:28px"><input type="checkbox" data-all></th>' : '') + th('rank', '#', 1) + th('name', 'Site') + cols.join('') + '</tr>';
  const body = rows.map(r => '<tr data-row="' + esc(r.key) + '" class="' + (S.sel === r.key ? 'sel' : '') + '">' + (chk ? '<td><input type="checkbox" data-check="' + esc(r.key) + '"' + (S.checked.has(r.key) ? ' checked' : '') + '></td>' : '') + site(r) + cells(r) + '</tr>').join('');
  const el = $('#list'), tb = el._head === head && el.querySelector('tbody'), w = wait ? '<div class="empty">' + wait + '</div>' : '';
  // Same header → only swap the body, so header tooltips don't flicker while rows stream in.
  if (tb) { tb.innerHTML = body; el.querySelector(':scope > .empty')?.remove(); if (w) el.insertAdjacentHTML('beforeend', w); }
  else { el.innerHTML = '<table><thead>' + head + '</thead><tbody>' + body + '</tbody></table>' + w; el._head = head; }
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
        g.append('path').attr('d', path(topojson.feature(us, us.objects.nation))).attr('fill', '#fff');
        g.append('path').attr('d', path(topojson.mesh(us, us.objects.states, (a, b) => a !== b))).attr('fill', 'none').attr('stroke', '#BFCCDD').attr('stroke-width', .8); };
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
    '<div class="lbl">Research office</div>' + (c.contact_url ? '<div class="kv"><div>Page</div><div><a href="' + esc(c.contact_url) + '" target="_blank" rel="noopener noreferrer">' + esc(c.contact_domain || c.contact_url) + ' ↗</a></div><div>Loads</div><div class="' + (c.url_status && c.url_status < 400 || c.url_status === 403 ? 'b-ok' : 'b-warn') + '">' + (c.url_status ? (c.url_status === 403 ? '✓ (403, bot-blocked)' : c.url_status < 400 ? '✓ ' + c.url_status : '✗ ' + c.url_status) : 'not checked') + '</div></div>' : '<div class="sub">None found</div>');
}
// a button that's really a checkbox: tracks whether the questionnaire went out (nothing is sent from here)
const sentBtn = k => '<label class="sbtn chkbtn' + (S.sent[k] ? ' on' : '') + '"><input type="checkbox" data-sent="' + esc(k) + '"' + (S.sent[k] ? ' checked' : '') + '>Sent</label>';
const COPY_ICON = '<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M3.5 10.5h-.5A1.5 1.5 0 0 1 1.5 9V3A1.5 1.5 0 0 1 3 1.5h6A1.5 1.5 0 0 1 10.5 3v.5" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>';
// the questionnaire as the plain-text email a coordinator would paste into their mail client
function mailText(r) {
  const qs = RUN.stage3.questionnaire, c = r.contact, to = c && c.route !== 'office' ? 'Dr. ' + c.pi.split(' ').pop() : r.name + ' research office';
  return 'Subject: Feasibility questionnaire: ' + RUN.trial.name + ' (' + RUN.trial.nct + ')\n\nHello ' + to + ',\n\nPlease answer the ' + qs.length + ' questions below for ' + RUN.trial.name + ' (' + RUN.trial.nct + ').\n\n' +
    qs.map((q, i) => (i + 1) + '. ' + q.question).join('\n') + '\n\nThank you,\n' + RUN.trial.sponsor + '\n';
}
function copyText(text, done) {
  const fallback = () => { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch (e) {} ta.remove(); done(ok); };
  navigator.clipboard && window.isSecureContext ? navigator.clipboard.writeText(text).then(() => done(true), fallback) : fallback();
}
function copyMail(btn) {
  const r = ROWS.find(x => x.key === btn.dataset.copymail), label = btn.querySelector('span');
  copyText(mailText(r), ok => { label.textContent = ok ? 'Copied' : 'Copy failed'; btn.classList.toggle('ok', ok); setTimeout(() => { label.textContent = 'Copy email'; btn.classList.remove('ok'); }, 1600); });
}
function sideQuest(r) {
  const qs = RUN.stage3.questionnaire, notes = r.answers.filter(a => a.q_id === 'NOTE');
  const src = a => a.source ? '<div class="pq-src">' + esc(a.source.split(';').map(x => x.trim()).join(', ')) + '</div>' : '';
  return '<div class="row-sb"><span class="sub">' + r.nAns + ' of ' + r.nQ + ' answered' + (r.net ? ' from site files' : ' from public records') + ' · ' + (r.nQ - r.nAns) + ' need a human</span>' +
    '<span class="acts"><button class="sbtn" data-copymail="' + esc(r.key) + '">' + COPY_ICON + '<span>Copy email</span></button>' + sentBtn(r.key) + '</span></div>' +
    qs.map(q => { const a = r.answers.find(x => x.q_id === q.id) || {}, h = isHuman(a);
      return '<div class="pq"><div class="pq-q"><span class="pq-id">' + esc(q.id) + '</span>' + esc(q.question) + '</div>' +
        '<div class="pq-a' + (h ? ' open' : '') + '">' + (h ? 'Needs a human' : esc(a.answer)) + '</div>' +
        (a.note ? '<div class="pq-why">' + esc(a.note) + '</div>' : '') + src(a) + '</div>'; }).join('') +
    (notes.length ? '<div class="lbl" style="padding-top:6px">Notes</div>' + notes.map(a => '<div class="pq"><div class="pq-q">' + esc(a.answer) + '</div>' + src(a) + '</div>').join('') : '');
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
  if (t.closest('[data-copymail]')) { copyMail(t.closest('[data-copymail]')); return; }
  if (t.closest('.chkbtn') && !t.matches('[data-sent]')) return;   // label click: the browser re-clicks the checkbox, handle it there
  if (t.matches('[data-sent]')) { const k = t.dataset.sent; t.checked ? S.sent[k] = true : delete S.sent[k]; store.set(SKEY, S.sent); draw(); return; }
  if (t.matches('[data-check]')) { t.checked ? S.checked.add(t.dataset.check) : S.checked.delete(t.dataset.check); draw(); return; }
  if (t.matches('[data-all]')) { document.querySelectorAll('[data-check]').forEach(x => t.checked ? S.checked.add(x.dataset.check) : S.checked.delete(x.dataset.check)); draw(); return; }
  if (t.closest('[data-answer]')) { openClient(t.closest('[data-answer]').dataset.answer); return; }
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

// ---------------------------------------------------------------- client side: the site agent answering the sponsor's questionnaire
// Proprietary comes from where the evidence lives: docs/confidential/ vs docs/public/ (site_data layout).
// Old runs without that layout fall back to a filename guess: capabilities sheets and CVs count as shareable.
const NOT_PROPRIETARY = /^(capabilities|cv_)/i;
const srcList = a => (a.source || '').split(';').map(x => x.trim()).filter(Boolean);
const evid = a => (a.evidence || []).filter(e => e && e.file && e.quote);
const fileProp = f => /^confidential\//.test(f) ? true : /^public\//.test(f) ? false : !NOT_PROPRIETARY.test(f.split('/').pop());
const isProp = a => (evid(a).length ? evid(a).map(e => e.file) : srcList(a)).some(fileProp);
const fmtDur = s => s >= 60 ? Math.round(s / 60) + ' min' : Math.round(s) + ' sec';
const needsHuman = a => /^y/i.test(a.needs_human || '') || !a.answer;
const docs = () => (RUN.stage3 && RUN.stage3.site_docs) || {};
// does the quote really appear in the file? exact first, then ignoring whitespace differences
function locate(text, quote) {
  const i = text.indexOf(quote); if (i >= 0) return [i, i + quote.length];
  const norm = quote.trim().replace(/\s+/g, ' '); if (!norm) return null;
  const re = new RegExp(norm.split(' ').map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+'));
  const m = re.exec(text); return m ? [m.index, m.index + m[0].length] : null;
}
let CFILES = [], CDROP = [], cTimer = null, C = { key: null, sel: null, file: null, view: 'mail' };
function openClient(key) {
  const site = RUN.stage3.sites.find(x => x.key === key), ans = RUN.stage3.answers[key] || [];
  C = { key, sel: null, file: null, view: 'mail', site, ans };
  $('#csite').textContent = site.name;
  CFILES = Object.keys(docs()).length ? Object.keys(docs()).sort() : [...new Set(ans.flatMap(a => evid(a).map(e => e.file).concat(srcList(a))))].sort();
  drawCFiles(); drawLeft();
  let n = 0; clearTimeout(cTimer);
  const step = () => { C.n = n; drawDraft(); if (n < RUN.stage3.questionnaire.length) { n++; cTimer = setTimeout(step, 250 + Math.random() * 450); } };
  step();
  $('#cgo').onclick = sendReply;
  $('#track').classList.add('client-on');
}
// the drafted reply as plain text: answers only (evidence and internal notes never leave the site)
function replyText() {
  const qs = RUN.stage3.questionnaire, notes = C.ans.filter(a => a.q_id === 'NOTE' && a.answer && !needsHuman(a));
  return 'Subject: Re: Feasibility questionnaire: ' + RUN.trial.name + ' (' + RUN.trial.nct + ')\n\nHello,\n\nOur answers to your ' + qs.length + ' questions are below.\n\n' +
    qs.map((q, i) => { const a = C.ans.find(x => x.q_id === q.id) || {};
      return (i + 1) + '. ' + q.question + '\n' + (a.answer && !needsHuman(a) ? a.answer : 'To follow: our team is confirming this one.'); }).join('\n\n') +
    (notes.length ? '\n\nAlso worth knowing:\n' + notes.map(a => '- ' + a.answer).join('\n') : '') + '\n\nBest,\n' + C.site.name + ' research office\n';
}
// Send = copy the reply to the clipboard, say so, then hand back to the sponsor side
function sendReply() {
  const btn = $('#cgo'), tip = $('#cgotip');
  copyText(replyText(), ok => {
    tip.textContent = ok ? 'Copied to clipboard' : 'Couldn\'t copy'; tip.classList.add('show');
    setTimeout(() => { tip.classList.remove('show'); if (ok) closeClient(); }, ok ? 1100 : 1800);
  });
}
function closeClient() { clearTimeout(cTimer); $('#track').classList.remove('client-on'); }
function drawDraft() {
  const qs = RUN.stage3.questionnaire, n = C.n;
  $('#cdraft').innerHTML = qs.map((q, i) => {
    const a = C.ans.find(x => x.q_id === q.id) || {}, h = needsHuman(a), g = evid(a).length > 0;
    if (i >= n) return '<div class="da pending"><div class="da-q">' + (i + 1) + '. ' + esc(q.question) + '</div><div class="da-h">…</div></div>';
    return '<div class="da' + (g ? ' grounded' : '') + (C.sel === q.id ? ' on' : '') + '"' + (g ? ' data-cq="' + esc(q.id) + '"' : '') + '><div class="da-q">' + (i + 1) + '. ' + esc(q.question) + '</div>' +
      (a.answer ? '<div class="da-a"><mark class="' + (isProp(a) ? 'prop' : 'pub') + '">' + esc(a.answer) + '</mark></div>' : '') +
      (h ? '<div class="da-h"><b>Needs a human.</b> ' + esc(a.note || '') + '</div>' : a.note ? '<div class="da-h">' + esc(a.note) + '</div>' : '') +
      (g ? '<div class="da-src">' + evid(a).length + ' quote' + (evid(a).length > 1 ? 's' : '') + ' ›</div>' : '') + '</div>';
  }).join('');
  const ok = qs.slice(0, n).filter(q => !needsHuman(C.ans.find(x => x.q_id === q.id) || {})).length;
  $('#cstat').textContent = n < qs.length ? 'Drafting ' + n + ' of ' + qs.length + '…' : qs.length + ' drafted · ' + ok + ' answered · ' + (qs.length - ok) + ' need a human';
  $('#cgo').disabled = n < qs.length;
}
// left card: the email, or (after clicking a grounded answer or a file) the file with the quoted lines highlighted
function drawLeft() {
  const qs = RUN.stage3.questionnaire;
  const LOGS = [['log-pub', 'Public Q&amp;A log', 'public/qa_log.md'], ['log-conf', 'Confidential Q&amp;A log', 'confidential/qa_log.md']].filter(l => docs()[l[2]] != null);
  const sw = LOGS.length ? '<div class="lsw">' + [['mail', 'Email']].concat(LOGS).map(([v, l]) => '<button data-cview="' + v + '" class="' + (C.view === v ? 'on' : '') + '">' + l + '</button>').join('') + '</div>' : '';
  const log = LOGS.find(l => l[0] === C.view);
  if (!C.file && log) { $('#cleft').innerHTML = sw + textFileHTML(log[2], docs()[log[2]]); return; }
  if (!C.file) {
    $('#cleft').innerHTML = sw + '<div class="mail-subj">Feasibility questionnaire: ' + esc(RUN.trial.name) + '</div>' +
      '<div class="mail-meta"><div><b>' + esc(RUN.trial.sponsor) + '</b> <span>to ' + esc(C.site.name) + '</span></div><span>' + esc(RUN.recorded || '') + '</span></div>' +
      '<div class="mail-body"><p>Dear ' + esc(C.site.short || C.site.name) + ' team,</p>' +
      '<p>As part of site selection for ' + esc(RUN.trial.name) + ' (' + esc(RUN.trial.nct) + '), please answer the ' + qs.length + ' questions below. Let us know if anything needs clarification.</p><ol>' + qs.map(q => '<li>' + esc(q.question) + '</li>').join('') + '</ol>' +
      '<p>Thank you,<br>Clinical Operations, ' + esc(RUN.trial.sponsor) + '</p></div>';
    return;
  }
  const a = C.sel ? C.ans.find(x => x.q_id === C.sel) || {} : {}, ev = evid(a), files = [...new Set(ev.map(e => e.file))], text = docs()[C.file];
  let body;
  if (text == null) body = '<div class="doc-miss">This file isn\'t in the run data, so it can\'t be shown.</div>';
  else {
    const spans = ev.filter(e => e.file === C.file).map(e => ({ e, at: locate(text, e.quote) }));
    const hits = spans.filter(x => x.at).sort((x, y) => x.at[0] - y.at[0]), cls = fileProp(C.file) ? 'prop' : 'pub';
    let out = '', pos = 0;
    hits.forEach(({ at }) => { if (at[0] < pos) return; out += esc(text.slice(pos, at[0])) + '<mark class="' + cls + '">' + esc(text.slice(at[0], at[1])) + '</mark>'; pos = at[1]; });
    body = spans.filter(x => !x.at).map(x => '<div class="doc-miss">Quote not found in this file: “' + esc(x.e.quote.slice(0, 120)) + '”</div>').join('') + '<pre class="doc">' + out + esc(text.slice(pos)) + '</pre>';
  }
  $('#cleft').innerHTML = '<div class="doc-h"><button class="doc-back" data-cback>← Back to email</button>' +
    (C.sel ? '<div class="ctitle">' + esc((qs.findIndex(q => q.id === C.sel) + 1) + '. ' + (qs.find(q => q.id === C.sel) || {}).question) + '</div>' : '') +
    (files.length > 1 ? '<div class="doc-files">' + files.map(f => '<button class="doc-file' + (f === C.file ? ' on' : '') + '" data-cfile="' + esc(f) + '">' + esc(f) + '</button>').join('') + '</div>'
      : '<div class="doc-files"><span class="doc-file on">' + esc(C.file) + '</span></div>') +
    '<div class="doc-tag">' + (fileProp(C.file) ? 'Confidential: internal site record' : 'Public: anyone can see this') + '</div></div>' + body;
  const m = $('#cleft mark'); if (m) m.scrollIntoView({ block: 'center' });
}
// a log file shown as the plain text file it is: one size, one spacing, lines as written
// display only (the file is untouched): no em dashes, each "|" field on its own line, a blank line between original lines
const logDisplay = text => text.trim().replace(/\s*\u2014\s*/g, ' ').split('\n').map(l => l.split(/\s*\|\s*/).join('\n')).join('\n\n').replace(/\n{3,}/g, '\n\n');
// public log: Q/A lines bold, the line just above each Q (the sponsor) plain, everything else italic
const styleLog = t => t.split('\n').map((l, i, ls) => /^[QA]: /.test(l) ? '<b>' + l + '</b>' : !l || /^Q: /.test(ls[i + 1]) ? l : '<i>' + l + '</i>').join('\n');
function textFileHTML(path, text) {
  return '<div class="tf"><div class="tf-h"><span class="mono">' + esc(path) + '</span><span>' + (new Blob([text]).size / 1024).toFixed(1) + ' KB · ' + text.split('\n').filter(l => /^\d{4}-\d\d-\d\d/.test(l)).length + ' entries</span></div>' +
    '<div class="tf-body">' + (path === 'public/qa_log.md' ? styleLog : x => x)(esc(logDisplay(text))) + '</div></div>';
}
function drawCFiles(flash) {
  $('#cfiles').innerHTML = CFILES.concat(CDROP.filter(f => !CFILES.includes(f))).map(f => '<li data-cdoc="' + esc(f) + '"' + (f === flash ? ' class="flash"' : '') + ' title="' + esc(f) + '">' + esc(f) + '</li>').join('');
}
// dropped files are only listed for now (a duplicate name just "updates" in place)
function initClientDrop() {
  const btn = $('#cdrop'), add = names => { names.forEach(n => { if (!CDROP.includes(n)) CDROP.push(n); }); drawCFiles(names[names.length - 1]); };
  ['dragenter', 'dragover'].forEach(ev => btn.addEventListener(ev, e => { e.preventDefault(); btn.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => btn.addEventListener(ev, e => { e.preventDefault(); btn.classList.remove('over'); }));
  btn.addEventListener('drop', e => add([...e.dataTransfer.files].map(f => f.name)));
  $('#cpick').onchange = e => add([...e.target.files].map(f => f.name));
  // clicks inside the client page: answer → its evidence, file chip/list item → that file, back → email
  $('#client').addEventListener('click', e => {
    const q = e.target.closest('[data-cq]'), f = e.target.closest('[data-cfile],[data-cdoc]'), back = e.target.closest('[data-cback]');
    if (q) { const a = C.ans.find(x => x.q_id === q.dataset.cq); C.sel = q.dataset.cq; C.file = evid(a)[0].file; drawDraft(); drawLeft(); }
    else if (f) { const name = f.dataset.cfile || f.dataset.cdoc; if (f.dataset.cdoc) C.sel = null; const lv = { 'public/qa_log.md': 'log-pub', 'confidential/qa_log.md': 'log-conf' }[name]; if (lv && !C.sel) { C.view = lv; C.file = null; } else C.file = name; drawDraft(); drawLeft(); }
    else if (back) { C.sel = null; C.file = null; drawDraft(); drawLeft(); }
    else if (e.target.closest('[data-cview]')) { C.view = e.target.closest('[data-cview]').dataset.cview; C.file = null; C.sel = null; drawDraft(); drawLeft(); }
  });
}
