#!/usr/bin/env python3
from pathlib import Path
import re
import json
import html

knowledge_root = Path('/Users/vineely/projects/trading-vy/knowledge')
wiki = knowledge_root / 'wiki'
out_html = knowledge_root / 'trading-knowledge-workspace.html'


def parse_frontmatter_and_body(text: str):
    text = text.replace('\r\n', '\n')
    fm = {}
    body = text
    if text.startswith('---\n'):
        end = text.find('\n---\n', 4)
        if end != -1:
            fm_text = text[4:end]
            body = text[end + 5:]
            for line in fm_text.split('\n'):
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k = k.strip()
                v = v.strip()
                if v.startswith('[') and v.endswith(']'):
                    inner = v[1:-1].strip()
                    if not inner:
                        fm[k] = []
                    else:
                        fm[k] = [item.strip().strip('"\'') for item in inner.split(',')]
                else:
                    fm[k] = v.strip('"')
    return fm, body.strip()


def slugify(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'page'


def replace_wikilinks(text: str):
    def repl(m):
        label = m.group(1)
        target = slugify(label)
        return f'<a href="#page={target}" class="inline-link">{html.escape(label)}</a>'
    return re.sub(r'\[\[([^\]]+)\]\]', repl, text)


def md_inline(text: str):
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    return replace_wikilinks(text)


def markdown_to_html(body: str):
    lines = body.split('\n')
    out = []
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_list:
                out.append('</ul>')
                in_list = False
            continue
        if stripped.startswith('# '):
            if in_list:
                out.append('</ul>')
                in_list = False
            continue
        if stripped.startswith('### '):
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f"<h3>{md_inline(stripped[4:])}</h3>")
        elif stripped.startswith('## '):
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f"<h2>{md_inline(stripped[3:])}</h2>")
        elif re.match(r'^\d+\.\s+', stripped):
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f"<p class=\"numbered\">{md_inline(stripped)}</p>")
        elif stripped.startswith('- '):
            if not in_list:
                out.append('<ul>')
                in_list = True
            out.append(f"<li>{md_inline(stripped[2:])}</li>")
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f"<p>{md_inline(stripped)}</p>")
    if in_list:
        out.append('</ul>')
    return '\n'.join(out)


def sectionize(body: str):
    sections = []
    current_title = 'Summary'
    current_lines = []
    for line in body.split('\n'):
        if line.startswith('# '):
            continue
        if line.startswith('## '):
            if current_lines:
                sections.append((current_title, '\n'.join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, '\n'.join(current_lines).strip()))
    return [(title, markdown_to_html(content)) for title, content in sections if content.strip()]


def load_page(path: Path, page_type_override=None, group=None):
    text = path.read_text(encoding='utf-8')
    fm, body = parse_frontmatter_and_body(text)
    title = fm.get('title') or path.stem.replace('-', ' ').title()
    page_type = page_type_override or fm.get('type', 'note')
    pid = path.stem
    tags = fm.get('tags', []) if isinstance(fm.get('tags', []), list) else []
    sections = sectionize(body)
    plain = re.sub(r'\s+', ' ', re.sub(r'[#*`\[\]\-]', ' ', body)).strip()
    return {
        'id': pid,
        'title': title,
        'type': page_type,
        'group': group or page_type,
        'tags': tags,
        'sections': sections,
        'search_text': ' '.join([title, page_type, ' '.join(tags), plain]),
        'meta': {
            'created': fm.get('created', ''),
            'updated': fm.get('updated', ''),
            'part': fm.get('part', ''),
            'pages': fm.get('pages', ''),
            'book': fm.get('book', ''),
        }
    }


def infer_author(page_id):
    if 'chan' in page_id:
        return 'Ernest P. Chan'
    if 'carver' in page_id:
        return 'Robert Carver'
    if 'clenow' in page_id or 'stocks-on-the-move' in page_id or 'following-the-trend' in page_id:
        return 'Andreas F. Clenow'
    return ''


pages = []
overview_page = load_page(wiki / 'overview.md', page_type_override='home', group='start')
pages.append(overview_page)

for p in sorted((wiki / 'sources').glob('*.md')):
    if p.name == 'systematic-trading-carver-chapter-map.md':
        pages.append(load_page(p, page_type_override='chapter-map', group='carver'))
    else:
        pages.append(load_page(p, page_type_override='book', group='books'))

for p in sorted((wiki / 'sources' / 'systematic-trading-carver-chapters').glob('*.md')):
    pages.append(load_page(p, page_type_override='chapter', group='carver'))

for p in sorted((wiki / 'concepts').glob('*.md')):
    pages.append(load_page(p, page_type_override='concept', group='concepts'))

for p in sorted((wiki / 'syntheses').glob('*.md')):
    pages.append(load_page(p, page_type_override='synthesis', group='syntheses'))

for p in pages:
    p['author'] = infer_author(p['id']) if p['type'] == 'book' else ''

home_data = {
    'start_here': [
        'reading-path',
        'strategy-research-pipeline',
        'systematic-trading-carver',
        'quantitative-trading-chan',
        'testing-and-execution-checklist'
    ],
    'books': [p['id'] for p in pages if p['type'] == 'book'],
    'concepts': [p['id'] for p in pages if p['type'] == 'concept'],
    'syntheses': [p['id'] for p in pages if p['type'] == 'synthesis'],
    'carver_priority': [
        'carver-st-03-fitting',
        'carver-st-09-volatility-targeting',
        'carver-st-10-position-sizing',
        'carver-st-11-portfolios',
        'carver-st-12-speed-and-size'
    ]
}

counts = {
    'books': len([p for p in pages if p['type'] == 'book']),
    'concepts': len([p for p in pages if p['type'] == 'concept']),
    'syntheses': len([p for p in pages if p['type'] == 'synthesis']),
    'chapters': len([p for p in pages if p['type'] == 'chapter']),
}

html_doc = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Trading Knowledge Workspace</title>
  <style>
    :root {
      --bg:#f7f6f3; --surface:#ffffff; --surface-2:#faf9f6; --border:#e8e5df; --text:#1a1917; --muted:#7a7670;
      --accent:#2d6a4f; --accent-lt:#d8f0e4; --warn:#b45309; --warn-lt:#fef3c7; --blue:#3730a3; --blue-lt:#eef2ff;
      --inr:#5b2d8c; --inr-lt:#ede9fe; --danger:#991b1b; --danger-lt:#fee2e2;
      --shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04); --shadow-md:0 4px 12px rgba(0,0,0,.07);
      --sidebar:320px;
    }
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    html{scroll-behavior:smooth}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5;min-height:100vh}
    a{color:inherit;text-decoration:none}
    code{background:#f3f1ed;border:1px solid var(--border);padding:1px 5px;border-radius:6px;font-size:12px}
    .app{display:grid;grid-template-columns:var(--sidebar) 1fr;min-height:100vh}
    .sidebar{position:sticky;top:0;height:100vh;padding:24px 18px 28px;border-right:1px solid var(--border);background:rgba(247,246,243,.92);backdrop-filter:saturate(120%) blur(12px);overflow:auto}
    .content{padding:32px 28px 56px;max-width:1100px;width:100%;margin:0 auto}
    .workspace-title{font-size:22px;font-weight:650;letter-spacing:-.3px;cursor:pointer}
    .subtitle{color:var(--muted);font-size:13px;margin-top:6px}
    .fx-pill{display:inline-block;background:#f0f0ee;color:var(--muted);font-size:11px;padding:3px 10px;border-radius:20px;margin-top:10px}
    .search{margin-top:18px}
    .search input{width:100%;border:1px solid var(--border);border-radius:10px;padding:10px 12px;background:#fff;font:inherit;color:var(--text)}
    .filter-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}
    .filter-pill{font-size:11px;font-weight:600;letter-spacing:.3px;padding:6px 10px;border-radius:999px;border:1px solid var(--border);background:#fff;color:var(--muted);cursor:pointer;transition:.15s}
    .filter-pill.active{background:var(--accent-lt);color:var(--accent);border-color:transparent}
    .nav-group{margin-top:20px}
    .section-title{font-size:11px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
    .nav-list{display:flex;flex-direction:column;gap:4px}
    .nav-item{padding:9px 10px;border-radius:10px;cursor:pointer;transition:.15s;border:1px solid transparent}
    .nav-item:hover{background:#fbfaf7;border-color:var(--border)}
    .nav-item.active{background:var(--surface);border-color:var(--border);box-shadow:var(--shadow)}
    .nav-item .name{font-size:13px;font-weight:550;color:var(--text)}
    .nav-item .meta{font-size:11px;color:var(--muted);margin-top:2px}
    .hero{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:24px 28px;display:flex;align-items:flex-start;justify-content:space-between;gap:20px;box-shadow:var(--shadow-md);flex-wrap:wrap}
    .hero .main{flex:1;min-width:240px}
    .hero .label{font-size:12px;color:var(--muted);margin-bottom:4px}
    .hero .amount{font-size:32px;font-weight:700;letter-spacing:-1px}
    .hero .note{font-size:12px;color:var(--muted);margin-top:6px;max-width:72ch}
    .hero-splits{display:flex;gap:10px;flex-wrap:wrap}
    .split{text-align:center;padding:10px 16px;border-radius:10px;background:var(--accent-lt);min-width:110px}
    .split.warn{background:var(--warn-lt)} .split.blue{background:var(--blue-lt)} .split.inr{background:var(--inr-lt)}
    .split .s-label{font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--muted);margin-bottom:2px;text-transform:uppercase}
    .split .s-amount{font-size:18px;font-weight:700}
    .grid{display:grid;gap:12px}
    .grid.books{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
    .grid.cards{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
    .card,.panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow)}
    .card.clickable{cursor:pointer;transition:transform .12s ease, box-shadow .12s ease, border-color .12s ease}
    .card.clickable:hover{transform:translateY(-1px);box-shadow:var(--shadow-md);border-color:#ded8cf}
    .card-top{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
    .card-title{font-size:14px;font-weight:650;letter-spacing:-.1px}
    .card-copy{font-size:12px;color:var(--muted)}
    .card-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;background:#f0f0ee}
    .tag{font-size:10px;font-weight:600;letter-spacing:.4px;padding:3px 8px;border-radius:20px;text-transform:uppercase}
    .tag.book{background:var(--blue-lt);color:var(--blue)} .tag.concept{background:var(--accent-lt);color:var(--accent)} .tag.synthesis{background:var(--warn-lt);color:var(--warn)} .tag.chapter{background:var(--inr-lt);color:var(--inr)}
    .section{margin-top:28px}
    .section-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;flex-wrap:wrap}
    .section-head .section-title{margin-bottom:0}
    .page-shell{display:flex;flex-direction:column;gap:16px}
    .page-head{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:24px 28px;box-shadow:var(--shadow-md)}
    .page-title{font-size:28px;font-weight:700;letter-spacing:-.8px}
    .page-sub{font-size:13px;color:var(--muted);margin-top:6px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
    .chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px}
    .chip{font-size:11px;font-weight:600;padding:4px 9px;border-radius:20px;background:#f0f0ee;color:#555}
    .content-grid{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:14px;align-items:start}
    .article{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:22px 24px;box-shadow:var(--shadow)}
    .article h2{font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin:22px 0 10px}
    .article h3{font-size:15px;font-weight:650;margin:18px 0 8px}
    .article p{margin:0 0 10px;font-size:14px}
    .article p.numbered{padding-left:2px;font-weight:500}
    .article ul{margin:0 0 14px 18px}
    .article li{margin:0 0 8px}
    .inline-link{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(45,106,79,.28)}
    .aside{display:flex;flex-direction:column;gap:12px;position:sticky;top:24px}
    .stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
    .stat .label{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:6px}
    .stat .value{font-size:20px;font-weight:700;letter-spacing:-.5px}
    .result-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
    .empty{background:#fffdf7;border:1px solid #e8e0c8;border-radius:12px;padding:18px 20px;font-size:13px;color:#5a5040;line-height:1.7}
    .breadcrumbs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:12px;color:var(--muted)}
    .toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}
    .button{border:1px solid var(--border);background:#fff;border-radius:10px;padding:8px 12px;font:inherit;font-size:12px;color:var(--text);cursor:pointer}
    .button:hover{background:#fbfaf7}
    .chapter-nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
    .chapter-nav a{display:inline-flex;padding:8px 10px;border-radius:10px;background:#fbfaf7;border:1px solid var(--border)}
    .home-subgrid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}
    .mini-list{display:flex;flex-direction:column;gap:10px}
    .mini-item{padding:10px 0;border-bottom:1px solid var(--border);cursor:pointer}
    .mini-item:last-child{border-bottom:0}
    .mini-item strong{display:block;font-size:13px}
    .mini-item span{font-size:12px;color:var(--muted)}
    .footer-note{margin-top:36px;text-align:center;font-size:12px;color:#b8b2aa}
    @media (max-width:980px){
      .app{grid-template-columns:1fr}
      .sidebar{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--border)}
      .content{padding:22px 14px 40px}
      .content-grid,.home-subgrid{grid-template-columns:1fr}
      .aside{position:relative;top:auto}
      .hero{padding:20px}
      .hero .amount{font-size:28px}
      .page-head{padding:20px}
      .page-title{font-size:24px}
    }
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="workspace-title" onclick="goHome()">Trading Knowledge</div>
    <div class="subtitle">Static local workspace for your quant strategy reading notes.</div>
    <div class="fx-pill">Books __BOOKS__ · Concepts __CONCEPTS__ · Chapters __CHAPTERS__</div>
    <div class="search"><input id="searchInput" type="text" placeholder="Search books, concepts, chapters..." /></div>
    <div class="filter-row" id="filters"></div>
    <div id="sidebarNav"></div>
  </aside>
  <main class="content">
    <div id="app"></div>
    <div class="footer-note">Generated from local trading knowledge notes · Open directly in browser, no server required.</div>
  </main>
</div>
<script>
const pages = __PAGES__;
const homeData = __HOME_DATA__;
let currentFilter = 'all';
let currentSearch = '';
const filterDefs = [['all','All'],['books','Books'],['concepts','Concepts'],['syntheses','Syntheses'],['carver','Carver Chapters']];
const groupLabels = {start:'Start Here',books:'Books',concepts:'Concepts',syntheses:'Syntheses',carver:'Carver Deep Dive'};

function stripTags(s){return s.replace(/<[^>]*>/g,' ');}
function pageMatchesFilter(p){if(currentFilter==='all')return true; if(currentFilter==='books')return p.type==='book'; if(currentFilter==='concepts')return p.type==='concept'; if(currentFilter==='syntheses')return p.type==='synthesis'; if(currentFilter==='carver')return p.type==='chapter'||p.type==='chapter-map'; return true;}
function pageMatchesSearch(p){if(!currentSearch)return true; return p.search_text.toLowerCase().includes(currentSearch);}
function visiblePages(){return pages.filter(p=>pageMatchesFilter(p)&&pageMatchesSearch(p));}
function currentPageId(){const hash=location.hash||''; const m=hash.match(/page=([^&]+)/); return m?decodeURIComponent(m[1]):'overview';}
function findPage(id){return pages.find(p=>p.id===id);}
function setRoute(id){location.hash='page='+encodeURIComponent(id);}
function goHome(){setRoute('overview');}
function escapeHtml(s){return String(s||'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));}
function copyPageLink(id){const url=location.origin+location.pathname+'#page='+encodeURIComponent(id); navigator.clipboard.writeText(url).then(()=>{const btn=document.getElementById('copy-link-btn'); if(btn){const old=btn.textContent; btn.textContent='Copied'; setTimeout(()=>btn.textContent=old,900);}});}
function renderFilters(){document.getElementById('filters').innerHTML=filterDefs.map(([key,label])=>`<button class="filter-pill ${currentFilter===key?'active':''}" onclick="setFilter('${key}')">${label}</button>`).join('');}
function setFilter(key){currentFilter=key; renderFilters(); renderSidebar(); renderMain();}
function renderSidebar(){const root=document.getElementById('sidebarNav'); const current=currentPageId(); const groups={start:[],books:[],concepts:[],syntheses:[],carver:[]}; visiblePages().forEach(p=>{if(groups[p.group])groups[p.group].push(p);}); root.innerHTML=Object.entries(groups).map(([group,items])=>{if(!items.length)return ''; const sorted=items.slice().sort((a,b)=>a.title.localeCompare(b.title)); return `<div class="nav-group"><div class="section-title">${groupLabels[group]}</div><div class="nav-list">${sorted.map(p=>`<div class="nav-item ${current===p.id?'active':''}" onclick="setRoute('${p.id}')"><div class="name">${escapeHtml(p.title)}</div><div class="meta">${escapeHtml(p.type.replace('-',' '))}</div></div>`).join('')}</div></div>`;}).join('');}
function iconForType(type){return ({book:'📘',concept:'🧠',synthesis:'🧭',chapter:'📑','chapter-map':'🗺️',home:'🏠'})[type]||'📄';}
function labelForType(type){return ({book:'Book',concept:'Concept',synthesis:'Synthesis',chapter:'Chapter','chapter-map':'Map',home:'Home'})[type]||type;}
function cardForPage(id,tagClass){const p=findPage(id); if(!p)return ''; const rawSummary=stripTags((p.sections[0]&&p.sections[0][1])||'').trim(); let summary=rawSummary; if(summary.length>165){summary=summary.slice(0,165); const lastSpace=summary.lastIndexOf(' '); if(lastSpace>100) summary=summary.slice(0,lastSpace); summary+='…';} return `<div class="card clickable" onclick="setRoute('${p.id}')"><div class="card-top"><div class="card-icon">${iconForType(p.type)}</div><span class="tag ${tagClass}">${escapeHtml(labelForType(p.type))}</span></div><div class="card-title">${escapeHtml(p.title)}</div><div class="card-copy">${escapeHtml(summary||'Open this note in the workspace.')}</div></div>`;}
function renderHome(){const overview=findPage('overview'); const overviewLead=overview&&overview.sections[0]?stripTags(overview.sections[0][1]).trim():'A compact workspace built from your trading book notes.'; const startRows=homeData.start_here.map(id=>{const p=findPage(id); if(!p)return ''; return `<div class="mini-item" onclick="setRoute('${p.id}')"><strong>${escapeHtml(p.title)}</strong><span>${escapeHtml(labelForType(p.type))} · Open this first when orienting to the library.</span></div>`;}).join(''); const priorityRows=homeData.carver_priority.map(id=>{const p=findPage(id); if(!p)return ''; const meta=((p.meta.pages||'')+(p.meta.pages?' · ':'')+'Carver deep dive'); return `<div class="mini-item" onclick="setRoute('${p.id}')"><strong>${escapeHtml(p.title)}</strong><span>${escapeHtml(meta)}</span></div>`;}).join(''); return `<div class="page-shell"><div class="hero"><div class="main"><div class="label">Workspace</div><div class="amount">Trading Knowledge Reference</div><div class="note">${escapeHtml(overviewLead)} Browse books, concepts, syntheses, and Carver chapter notes in a single local HTML workspace.</div></div><div class="hero-splits"><div class="split"><div class="s-label">Books</div><div class="s-amount">__BOOKS__</div></div><div class="split blue"><div class="s-label">Concepts</div><div class="s-amount">__CONCEPTS__</div></div><div class="split warn"><div class="s-label">Syntheses</div><div class="s-amount">__SYNTHESES__</div></div><div class="split inr"><div class="s-label">Carver chapters</div><div class="s-amount">__CHAPTERS__</div></div></div></div><div class="section home-subgrid"><div class="panel"><div class="section-title">Start here</div><div class="mini-list">${startRows}</div></div><div class="panel"><div class="section-title">Best next reading for implementation</div><div class="mini-list">${priorityRows}</div></div></div><div class="section"><div class="section-head"><div class="section-title">Books</div></div><div class="grid books">${homeData.books.map(id=>cardForPage(id,'book')).join('')}</div></div><div class="section"><div class="section-head"><div class="section-title">Key concepts</div></div><div class="grid cards">${homeData.concepts.map(id=>cardForPage(id,'concept')).join('')}</div></div><div class="section"><div class="section-head"><div class="section-title">Syntheses for actual research work</div></div><div class="grid cards">${homeData.syntheses.map(id=>cardForPage(id,'synthesis')).join('')}</div></div></div>`;}
function renderChapterNav(id){const chapters=pages.filter(p=>p.type==='chapter').sort((a,b)=>a.id.localeCompare(b.id)); const idx=chapters.findIndex(c=>c.id===id); const prev=idx>0?chapters[idx-1]:null; const next=idx<chapters.length-1?chapters[idx+1]:null; return `<div class="chapter-nav">${prev?`<a href="#page=${encodeURIComponent(prev.id)}">← ${escapeHtml(prev.title)}</a>`:''}${next?`<a href="#page=${encodeURIComponent(next.id)}">${escapeHtml(next.title)} →</a>`:''}</div>`;}
function renderPage(page){const metaBits=[page.type!=='home'?labelForType(page.type):'Home']; if(page.author)metaBits.push(page.author); if(page.meta.part)metaBits.push(page.meta.part); if(page.meta.pages)metaBits.push('pp. '+page.meta.pages); const chips=(page.tags||[]).map(tag=>`<span class="chip">${escapeHtml(tag)}</span>`).join(''); const article=page.sections.map(([title,content])=>`<h2>${escapeHtml(title)}</h2>${content}`).join(''); const searchScopeCount=visiblePages().length; const statPages=page.meta.pages?`<div class="stat"><div class="label">Pages</div><div class="value">${escapeHtml(page.meta.pages)}</div></div>`:''; const statPart=page.meta.part?`<div class="stat"><div class="label">Part</div><div class="value">${escapeHtml(page.meta.part)}</div></div>`:''; const chapterNav=page.type==='chapter'?renderChapterNav(page.id):''; return `<div class="page-shell"><div class="breadcrumbs"><span>Workspace</span><span>›</span><a href="#page=overview" class="inline-link">Home</a><span>›</span><span>${escapeHtml(page.title)}</span></div><div class="page-head"><div class="page-title">${escapeHtml(page.title)}</div><div class="page-sub">${metaBits.map(escapeHtml).join(' · ')}</div><div class="toolbar"><button class="button" onclick="goHome()">Back to home</button><button class="button" id="copy-link-btn" onclick="copyPageLink('${page.id}')">Copy link</button></div>${chips?`<div class="chips">${chips}</div>`:''}</div><div class="content-grid"><article class="article">${article}${chapterNav}</article><aside class="aside"><div class="stat"><div class="label">Type</div><div class="value">${escapeHtml(labelForType(page.type))}</div></div><div class="stat"><div class="label">Current filter scope</div><div class="value">${searchScopeCount}</div></div>${statPages}${statPart}</aside></div></div>`;}
function renderSearchResults(){const hits=visiblePages(); if(!hits.length){return `<div class="empty"><strong>No results.</strong> Try clearing the filter or using a broader search term like <code>risk</code>, <code>Carver</code>, or <code>momentum</code>.</div>`;} return `<div class="page-shell"><div class="page-head"><div class="page-title">Search & filter results</div><div class="page-sub">${hits.length} visible pages · filter ${escapeHtml(currentFilter)}${currentSearch?` · search “${escapeHtml(currentSearch)}”`:''}</div></div><div class="result-list">${hits.map(p=>cardForPage(p.id,p.type==='book'?'book':p.type==='concept'?'concept':p.type==='synthesis'?'synthesis':'chapter')).join('')}</div></div>`;}
function renderMain(){const root=document.getElementById('app'); const page=findPage(currentPageId()); if((currentSearch||currentFilter!=='all')&&(!page||currentPageId()==='overview')){root.innerHTML=renderSearchResults(); return;} if(!page){root.innerHTML=renderHome(); return;} if(page.type==='home'){root.innerHTML=renderHome(); return;} root.innerHTML=renderPage(page);}
function syncSearch(){currentSearch=document.getElementById('searchInput').value.trim().toLowerCase(); renderSidebar(); renderMain();}
document.getElementById('searchInput').addEventListener('input',syncSearch);
window.addEventListener('hashchange',()=>{renderSidebar(); renderMain();});
renderFilters(); renderSidebar(); renderMain();
</script>
</body>
</html>
"""

html_doc = html_doc.replace('__PAGES__', json.dumps(pages, ensure_ascii=False))
html_doc = html_doc.replace('__HOME_DATA__', json.dumps(home_data, ensure_ascii=False))
html_doc = html_doc.replace('__BOOKS__', str(counts['books']))
html_doc = html_doc.replace('__CONCEPTS__', str(counts['concepts']))
html_doc = html_doc.replace('__SYNTHESES__', str(counts['syntheses']))
html_doc = html_doc.replace('__CHAPTERS__', str(counts['chapters']))

out_html.write_text(html_doc, encoding='utf-8')
print(f'Generated {len(pages)} pages -> {out_html}')
