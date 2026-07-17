#!/usr/bin/env python3
"""Build self-contained index.html from data.min.json."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    data = (ROOT / "data.min.json").read_text(encoding="utf-8")
    b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Recycle Bin Randomizer</title>
<style>
  :root {{
    --bg: #0c0d10; --panel: #14161c; --panel2: #1a1d26; --border: #2a2f3a;
    --text: #e8eaef; --muted: #8b93a7; --accent: #5ed523; --accent2: #67c0f9; --warn: #ffb020;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    --sans: "Segoe UI", system-ui, -apple-system, sans-serif;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: var(--sans); background: var(--bg); color: var(--text); line-height: 1.45; min-height: 100vh; }}
  header {{ padding: 1.25rem 1.5rem 1rem; border-bottom: 1px solid var(--border); background: linear-gradient(180deg, #12141a, var(--bg)); }}
  header h1 {{ margin: 0 0 .35rem; font-size: 1.35rem; font-weight: 700; }}
  header p {{ margin: 0; color: var(--muted); font-size: .92rem; max-width: 72ch; }}
  header a {{ color: var(--accent2); }}
  .links-bar {{ margin: .65rem 0 0; font-size: .9rem; color: var(--muted); }}
  .links-bar a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
  .links-bar a:hover {{ text-decoration: underline; }}
  .links-bar .sep {{ margin: 0 .45rem; color: var(--border); }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 1rem 1.25rem 3rem; }}
  .hero {{ display: grid; gap: 1rem; margin: 1.25rem 0 1.5rem; }}
  @media (min-width: 800px) {{ .hero {{ grid-template-columns: 1.15fr .85fr; }} }}
  .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 1.1rem 1.2rem; }}
  .card h2 {{ margin: 0 0 .75rem; font-size: .78rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }}
  .out {{ font-family: var(--mono); font-size: 1.3rem; background: var(--panel2); border: 1px dashed var(--border); border-radius: 10px; padding: 1rem 1.1rem; min-height: 3.2rem; word-break: break-word; color: var(--accent); }}
  .meta-line {{ margin-top: .65rem; color: var(--muted); font-size: .88rem; }}
  .meta-line strong {{ color: var(--text); }}
  .row {{ display: flex; flex-wrap: wrap; gap: .6rem; margin-top: 1rem; align-items: center; }}
  button {{ appearance: none; border: 1px solid var(--border); background: var(--panel2); color: var(--text); border-radius: 9px; padding: .65rem 1rem; font: inherit; font-weight: 600; cursor: pointer; }}
  button.primary {{ background: var(--accent); color: #0a1206; border-color: transparent; }}
  button:hover {{ filter: brightness(1.06); }}
  label {{ display: flex; align-items: center; gap: .4rem; color: var(--muted); font-size: .9rem; }}
  select, input[type="search"] {{ background: var(--panel2); border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: .5rem .7rem; font: inherit; }}
  .toolbar {{ display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; margin: 0 0 1rem; justify-content: space-between; }}
  .toolbar .left {{ display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
  th, td {{ text-align: left; padding: .55rem .5rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; position: sticky; top: 0; background: var(--panel); z-index: 1; }}
  tr:hover td {{ background: rgba(255,255,255,.02); }}
  .tag {{ display: inline-block; font-size: .72rem; padding: .12rem .4rem; border-radius: 999px; background: #222833; margin-right: .25rem; }}
  .tag.m1 {{ color: #9dff6a; }} .tag.m2 {{ color: #67c0f9; }} .tag.m3 {{ color: #ffc46b; }}
  .range {{ font-family: var(--mono); color: var(--warn); font-size: .85rem; }}
  .credit {{ color: var(--muted); font-size: .82rem; }}
  .table-wrap {{ overflow: auto; max-height: 70vh; border: 1px solid var(--border); border-radius: 12px; background: var(--panel); }}
  footer {{ margin-top: 1.5rem; color: var(--muted); font-size: .82rem; }}
  footer a {{ color: var(--accent2); }}
  .toast {{ position: fixed; bottom: 1.2rem; right: 1.2rem; background: #1e3a12; color: var(--accent); border: 1px solid #3a6b1f; padding: .6rem .9rem; border-radius: 8px; opacity: 0; transition: opacity .2s; pointer-events: none; }}
  .toast.show {{ opacity: 1; }}
  .hint {{ font-size: .85rem; color: var(--muted); margin-top: .5rem; }}
  code {{ font-family: var(--mono); font-size: .85em; }}
</style>
</head>
<body>
<header>
  <div class="wrap" style="padding-top:0;padding-bottom:0">
    <h1>Recycle Bin Randomizer</h1>
    <p>
      Full listing of keyphrases from <a id="srcDoc" href="#" target="_blank" rel="noopener">KVN AUST’s maps</a>
      (Update 5.0). Generate a random search string (zero-padded numbers + real dates), copy, paste into YouTube.
    </p>
    <p class="links-bar">
      <a href="https://kvnaust.github.io/YouTube-NonBiasedVideoSearcher/" target="_blank" rel="noopener">Non-biased Video Searcher</a>
      <span class="sep">·</span>
      <a href="https://youtube.com/@kvnaust" target="_blank" rel="noopener">@KVNAUST on YouTube</a>
      <span class="sep">·</span>
      <a href="https://x.com/mingkastermk" target="_blank" rel="noopener">KVN AUST on X</a>
    </p>
  </div>
</header>
<div class="wrap">
  <div class="hero">
    <div class="card">
      <h2>Random search</h2>
      <div class="out" id="result" aria-live="polite">—</div>
      <div class="meta-line" id="resultMeta"></div>
      <div class="row">
        <button class="primary" id="btnGen" type="button">Generate random search</button>
        <button id="btnCopy" type="button">Copy</button>
        <button id="btnYt" type="button">Open on YouTube</button>
      </div>
      <div class="row" style="margin-top:.75rem">
        <label>Pool
          <select id="poolMap">
            <option value="all">All maps</option>
            <option value="map1">Map 1 — new</option>
            <option value="map2">Map 2 — old</option>
            <option value="map3">Map 3 — 2006–08</option>
            <option value="ranged">Only number-range entries</option>
            <option value="dates">Only date templates</option>
          </select>
        </label>
        <label><input type="checkbox" id="preferQuoted" checked /> Prefer quotes when the map uses them</label>
        <label><input type="checkbox" id="includeNsfw" /> Include NSFW-tagged leads</label>
      </div>
      <p class="hint">Map 1 → sort by <strong>Upload date</strong> (use the <a href="https://kvnaust.github.io/YouTube-NonBiasedVideoSearcher/" target="_blank" rel="noopener">non-biased searcher</a>). Map 2/3 → <strong>View count</strong>; try <code>Before:2015</code>.</p>
      <p class="hint">Padding: <code>XXXX</code> → <code>0057</code>. Dates: real calendar days for YYYYMMDD / YYYY MM DD / Month DD, YYYY / DDMMYY, etc.</p>
      <p class="hint" style="color:var(--warn)">Content notice: the source maps include a few NSFW search leads (playlist/bitrate keywords). They are <strong>excluded from random</strong> unless you enable “Include NSFW-tagged leads.” Exploring obscure uploads can surface anything — browse at your own risk.</p>
    </div>
    <div class="card">
      <h2>About</h2>
      <p style="margin:0;color:var(--muted);font-size:.92rem">
        Default device/app filenames that surface near-zero-view uploads.
        <span id="count"></span> leads parsed from the public Google Doc.
      </p>
      <p class="hint" id="attr"></p>
    </div>
  </div>

  <div class="toolbar">
    <div class="left">
      <label>Filter map
        <select id="filterMap">
          <option value="all">All</option>
          <option value="map1">Map 1</option>
          <option value="map2">Map 2</option>
          <option value="map3">Map 3</option>
        </select>
      </label>
      <input type="search" id="filterQ" placeholder="Filter title / source / credit…" style="min-width:16rem" />
    </div>
    <span class="credit" id="shownCount"></span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Map</th>
          <th>Title / keyphrase</th>
          <th>Range / date form</th>
          <th>Source</th>
          <th>Credit</th>
          <th>Example</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <footer><p id="footAttr"></p></footer>
</div>
<div class="toast" id="toast">Copied</div>
<script type="text/plain" id="DATA_B64">{b64}</script>
<script>
function b64ToUtf8(b64) {{
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder('utf-8').decode(bytes);
}}
const DATA = JSON.parse(b64ToUtf8(document.getElementById('DATA_B64').textContent.trim()));
const entries = DATA.entries;
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DATE_KINDS = new Set(['yyyymmdd','yyyy_mm_dd','yyyy_dash_mm_dd','ddmmyyyy','ddmmyy','mm_dd_yyyy','yyyy_mm','month_dd_yyyy','month_yyyy','year','ko_ymd','ja_ymd']);

function safeUrl(u) {{
  const s = String(u||'');
  return /^https?:\\/\\//i.test(s) ? s : '#';
}}
const SRC_DOC = safeUrl(DATA.meta.sourceDoc);
document.getElementById('srcDoc').href = SRC_DOC;
document.getElementById('count').textContent = DATA.meta.entryCount;
document.getElementById('attr').textContent =
  DATA.meta.attribution + ' ' + (DATA.meta.paddingRule||'') + ' ' + (DATA.meta.dateRule||'');
document.getElementById('footAttr').innerHTML =
  'Source: <a href="'+esc(SRC_DOC)+'" target="_blank" rel="noopener">'+esc(DATA.meta.sourceTitle)+'</a>. ' +
  esc(DATA.meta.attribution) +
  ' · <a href="https://kvnaust.github.io/YouTube-NonBiasedVideoSearcher/" target="_blank" rel="noopener">Non-biased Video Searcher</a>' +
  ' · <a href="https://youtube.com/@kvnaust" target="_blank" rel="noopener">@KVNAUST</a>' +
  ' · <a href="https://x.com/mingkastermk" target="_blank" rel="noopener">X @mingkastermk</a>';

function randInt(min, max) {{
  min = Math.ceil(min); max = Math.floor(max);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}}
function pad(n, w) {{
  const width = Math.max(0, w|0);
  let s = String(Math.trunc(Number(n)));
  if (width <= 0) return s;
  while (s.length < width) s = '0' + s;
  return s;
}}
function daysInMonth(y, m) {{ return new Date(y, m, 0).getDate(); }}
function randomYmd(yearMin, yearMax) {{
  const thisYear = new Date().getFullYear();
  const y0 = yearMin || 2008;
  let y1 = (yearMax == null ? thisYear : yearMax);
  y1 = Math.max(y0, Math.min(y1, thisYear));
  const y = randInt(y0, y1);
  const m = randInt(1, 12);
  const d = randInt(1, daysInMonth(y, m));
  return {{
    compact: ''+y+pad(m,2)+pad(d,2),
    spaced: y+' '+pad(m,2)+' '+pad(d,2),
    dashed: y+'-'+pad(m,2)+'-'+pad(d,2),
    ddmmyyyy: pad(d,2)+pad(m,2)+y,
    ddmmyy: pad(d,2)+pad(m,2)+pad(y%100,2),
    mm_dd_yyyy: pad(m,2)+' '+pad(d,2)+' '+y,
    yyyy_mm: y+' '+pad(m,2),
    long: MONTHS[m-1]+' '+pad(d,2)+', '+y,
    month_yyyy: MONTHS[m-1]+' '+y,
    ko: y+'년 '+m+'월 '+d+'일',
    ja: y+'年'+m+'月'+d+'日',
  }};
}}
function maybeQuote(s, quoted, prefer) {{
  if (prefer && quoted && !(s.startsWith('"') && s.endsWith('"'))) return '"'+s+'"';
  return s;
}}
function generateFrom(entry, preferQuoted) {{
  const t = entry.template;
  let s = t.prefix || t.raw_core || entry.title;
  const r = t.range || {{}};
  const yMin = t.yearMin || 2008;
  const yMax = t.yearMax;
  switch (t.kind) {{
    case 'fixed': break;
    case 'int':
    case 'int_append': {{
      const n = randInt(r.min ?? 0, r.max ?? 9999);
      const p = pad(n, (r.width != null ? r.width : String(r.max||0).length));
      s = (t.kind === 'int_append') ? (t.prefix + ' ' + p).trim() : t.prefix.replace('{{n}}', p);
      break;
    }}
    case 'dual_int': {{
      s = t.prefix
        .replace('{{a}}', pad(randInt(r.min1, r.max1), r.width1))
        .replace('{{b}}', pad(randInt(r.min2, r.max2), r.width2));
      break;
    }}
    case 'multi_int': {{
      s = t.prefix;
      const fields = t.fields || [];
      for (let i = 0; i < fields.length; i++) {{
        const f = fields[i];
        const n = randInt(f.min ?? 0, f.max ?? (Math.pow(10, f.width||1)-1));
        s = s.split('{{n'+i+'}}').join(pad(n, f.width||1));
      }}
      break;
    }}
    case 'hex2': {{
      const hex = '0123456789ABCDEF';
      let n = hex[randInt(0,15)] + hex[randInt(0,15)];
      const w = r.width || 2;
      while (n.length < w) n = '0' + n;
      s = t.prefix.replace('{{n}}', n.slice(0, w));
      break;
    }}
    case 'hhmmss':
      s = t.prefix.replace('{{n}}', pad(randInt(0,23),2)+pad(randInt(0,59),2)+pad(randInt(0,59),2));
      break;
    case 'yyyymmdd':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).compact); break;
    case 'yyyy_mm_dd':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).spaced); break;
    case 'yyyy_dash_mm_dd':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).dashed); break;
    case 'ddmmyyyy':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).ddmmyyyy); break;
    case 'ddmmyy':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).ddmmyy); break;
    case 'mm_dd_yyyy':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).mm_dd_yyyy); break;
    case 'yyyy_mm':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).yyyy_mm); break;
    case 'month_dd_yyyy':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).long); break;
    case 'month_yyyy':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).month_yyyy); break;
    case 'ko_ymd':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).ko); break;
    case 'ja_ymd':
      s = t.prefix.replace('{{date}}', randomYmd(yMin, yMax).ja); break;
    case 'year': {{
      const thisYear = new Date().getFullYear();
      const y1 = (yMax == null ? thisYear : yMax);
      s = t.prefix.replace('{{year}}', String(randInt(yMin, Math.max(yMin, Math.min(y1, thisYear)))));
      break;
    }}
    default: s = entry.title;
  }}
  s = s.replace(/\\{{[^}}]+\\}}/g, '').replace(/\\s+/g, ' ').trim();
  return maybeQuote(s, !!t.quoted, preferQuoted);
}}
function poolEntries() {{
  const mode = document.getElementById('poolMap').value;
  const nsfw = document.getElementById('includeNsfw').checked;
  return entries.filter(e => {{
    if (!nsfw && e.nsfw) return false;
    if (mode === 'all') return true;
    if (mode === 'ranged') return !!(e.template && e.template.range);
    if (mode === 'dates') return DATE_KINDS.has(e.template.kind);
    return e.map === mode;
  }});
}}
function generate() {{
  const pool = poolEntries();
  if (!pool.length) {{ alert('No entries in this pool'); return; }}
  const e = pool[randInt(0, pool.length-1)];
  const q = generateFrom(e, document.getElementById('preferQuoted').checked);
  document.getElementById('result').textContent = q;
  document.getElementById('resultMeta').innerHTML =
    '<strong>'+esc(e.mapTitle)+'</strong> · '+esc(e.title)+
    (e.rangeDisplay ? ' · <span class="range">'+esc(e.rangeDisplay)+'</span>' : '')+
    (e.source ? ' · '+esc(e.source) : '')+
    (e.credit ? ' · '+esc(e.credit) : '');
}}
function esc(s) {{
  return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
function toast(msg) {{
  const el = document.getElementById('toast');
  el.textContent = msg; el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 1200);
}}
async function copy() {{
  if (document.getElementById('result').textContent === '—') generate();
  const v = document.getElementById('result').textContent;
  try {{ await navigator.clipboard.writeText(v); toast('Copied'); }}
  catch {{ prompt('Copy:', v); }}
}}
function openYt() {{
  if (document.getElementById('result').textContent === '—') generate();
  const t = document.getElementById('result').textContent.replace(/^"|"$/g,'');
  window.open('https://www.youtube.com/results?search_query=' + encodeURIComponent(t), '_blank', 'noopener');
}}
function renderTable() {{
  const map = document.getElementById('filterMap').value;
  const q = document.getElementById('filterQ').value.trim().toLowerCase();
  const nsfw = document.getElementById('includeNsfw').checked;
  const rows = entries.filter(e => {{
    if (!nsfw && e.nsfw) return false;
    if (map !== 'all' && e.map !== map) return false;
    if (!q) return true;
    return [e.title, e.source, e.credit, e.example, e.rangeDisplay, e.mapTitle].join(' ').toLowerCase().includes(q);
  }});
  document.getElementById('shownCount').textContent = rows.length + ' shown / ' + entries.length;
  document.getElementById('tbody').innerHTML = rows.map(e => {{
    const mc = e.map === 'map1' ? 'm1' : e.map === 'map2' ? 'm2' : 'm3';
    const nsfwTag = e.nsfw ? ' <span class="tag" style="color:var(--warn)">nsfw</span>' : '';
    return '<tr><td><span class="tag '+mc+'">'+esc(e.map)+'</span>'+nsfwTag+'</td><td>'+esc(e.title)+'</td><td class="range">'+esc(e.rangeDisplay||'—')+
      '</td><td>'+esc(e.source||'—')+'</td><td class="credit">'+esc(e.credit||'')+'</td><td class="credit">'+esc(e.example||'')+'</td></tr>';
  }}).join('');
}}
document.getElementById('btnGen').onclick = generate;
document.getElementById('btnCopy').onclick = copy;
document.getElementById('btnYt').onclick = openYt;
document.getElementById('filterMap').onchange = renderTable;
document.getElementById('filterQ').oninput = renderTable;
document.getElementById('includeNsfw').onchange = () => {{ renderTable(); }};
renderTable();
generate();
</script>
</body>
</html>
"""
    # Fix double-brace issues in JS - the f-string doubled braces for CSS/JS.
    # Template placeholders in JS need single braces for .replace('{n}'...
    # I used '{{n}}' which becomes '{n}' in output - good for JS string.
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print("wrote index.html", (ROOT / "index.html").stat().st_size)


if __name__ == "__main__":
    main()
