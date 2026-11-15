#!/usr/bin/env python3
"""Controle van gevoelige inhoud: kloppen foto's, namen en links?

    python3 -I scripts/controleer_inhoud.py

Schrijft scripts/rapport-controle.txt. Verandert niets aan de site.

Controles:
 A. Foto's: komt elke foto op een pagina uit de eigen bronpagina (html/)?  (omzetfouten)
 B. Foto-naam vs pagina: komt iets van de bestandsnaam/mediatitel voor in de pagina?  (bronfouten)
 C. Linktekst vs doel: past de naam in de linktekst bij de URL (Joods Monument e.d.)?
 D. Galerijen: past de foto (naam op steen) bij de pagina waar hij naar linkt?
 E. Overzichtstabel: naam vs Joods Monument-link, locatie vs adreslink, naam op adrespagina, datum.
"""
import hashlib, html as H, json, re, sys, unicodedata, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'website'
MEDIA = json.loads((ROOT / 'content/media.json').read_text(encoding='utf-8'))
uit = []
def meld(*a): uit.append(' '.join(str(x) for x in a))

def norm(t):
    t = unicodedata.normalize('NFKD', H.unescape(t)).encode('ascii', 'ignore').decode().lower()
    return t
GENERIEK = set('''legging steenlegging stolperstein stolpersteine stenen steen foto achtergrond scaled img jpg jpeg png webp
enhanced kleur zw utrecht hier woonde bis bs van der de den het en vd ter te op voor in jpeg copy kopie edited
image afbeelding screenshot whatsapp scan bewerkt nieuw def final'''.split())
def tokens(t, min_len=3):
    return {w for w in re.findall(r'[a-z]+', norm(t)) if len(w) >= min_len and w not in GENERIEK}

def md_delen(p):
    s = p.read_text(encoding='utf-8')
    _, fm, body = s.split('---', 2)
    return fm, body

def sha(p): return hashlib.sha1(p.read_bytes()).hexdigest()

def media_titel(url):
    stam = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', url.rsplit('/', 1)[-1]).replace('-scaled', '').rsplit('.', 1)[0]
    for m in MEDIA:
        if m.get('link', '').rsplit('/', 1)[-1] == stam or m.get('link', '').rstrip('/').rsplit('/', 1)[-1] == stam:
            return (m.get('title') or '') + ' ' + (m.get('description') or '')
    return ''

def bron_bestanden(url):
    """Mogelijke lokale bestanden voor een upload-URL (origineel, scaled, formaat)."""
    m = re.search(r'wp-content/uploads/(.+)$', url)
    if not m: return []
    p = ROOT / 'media' / m.group(1)
    basis = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', p.name)
    return [x for x in [p.with_name(basis.replace('.', '-scaled.', 1)), p.with_name(basis), p] if x.exists()]

def bron_afbeeldingen(src):
    a = src.find('data-elementor-type="wp-page"'); b = src.find('data-elementor-type="footer"')
    main = src[a:b]
    urls = set(re.findall(r'background-image:\s*url\(\s*["\']?([^"\')]+uploads/[^"\')]+)', src))
    urls |= set(re.findall(r'<img[^>]+src="([^"]+uploads/[^"]+)"', main))
    urls |= set(H.unescape(u) for u in re.findall(r'data-thumbnail="([^"]+)"', main))
    urls |= set(re.findall(r'swiper-slide-bg\{[^}]*background-image:url\(([^)]+)\)', src))
    return {u for u in urls if not re.search(r'servaas|raster|logo|Raster', u)}

def pagina_afbeeldingen(md, fm, body):
    paden = re.findall(r'^\s*(?:-\s*)?foto:\s*(\S+)', fm, re.M) + re.findall(r'!\[[^\]]*\]\(([^)]+)\)', body)
    return [(md.parent / p).resolve() for p in paden]

# ---------- alle pagina's ----------
paginas = []
for map_, soort in [('adressen', 'adres'), ('paginas', None)]:
    for md in sorted((WEB / 'src/content' / map_).glob('*.md')):
        fm, body = md_delen(md)
        s = re.search(r'^soort:\s*(\w+)', fm, re.M)
        paginas.append({'md': md, 'fm': fm, 'body': body, 'soort': soort or (s.group(1) if s else '?'),
                        'slug': re.search(r'^slug:\s*(\S+)', fm, re.M).group(1),
                        'bron': (re.search(r'^bron:\s*(\S+)', fm, re.M) or [None, None])[1]})
per_slug = {p['slug']: p for p in paginas}
def paginatekst(p): return p['fm'] + ' ' + p['body']

# ---------- A + B: foto's ----------
meld('=== A. Foto\'s komen uit de eigen bronpagina (omzetcontrole)')
meld('=== B. Bestandsnaam/mediatitel van foto past bij de pagina')
fouten_a = 0
for p in paginas:
    if p['soort'] not in ('adres', 'persoon', 'video') and p['slug'] not in ('recent-gelegd', 'eerste'): continue
    afb = pagina_afbeeldingen(p['md'], p['fm'], p['body'])
    if not p['bron'] or not afb: continue
    bronnen = []
    for bestand in p['bron'].split(','):
        bp = ROOT / bestand.strip()
        if bp.exists(): bronnen.append(bp.read_text(encoding='utf-8'))
    bron_hash = {}
    for src in bronnen:
        for u in bron_afbeeldingen(src):
            for f in bron_bestanden(u):
                bron_hash[sha(f)] = u
    for a in afb:
        if not a.exists():
            meld(f'A! {p["slug"]}: bestand ontbreekt {a.name}'); fouten_a += 1; continue
        u = bron_hash.get(sha(a))
        if not u:
            meld(f'A? {p["slug"]}: {a.name} niet terug te vinden in de bronpagina (samengevoegd of met de hand toegevoegd?)'); fouten_a += 1; continue
        # B: naam van de foto vs pagina
        if p['slug'] in ('recent-gelegd', 'eerste'): continue
        ft = tokens(Path(u).stem + ' ' + media_titel(u))
        pt = tokens(paginatekst(p) + ' ' + p['slug'].replace('-', ' '))
        if ft and not (ft & pt):
            meld(f'B! {p["slug"]}: foto "{Path(u).name}" (titel: "{media_titel(u).strip()}") — geen naam/adres uit de foto komt voor op de pagina')
meld(f'   ({fouten_a} meldingen bij A)')

# ---------- C: linktekst vs doel ----------
meld('\n=== C. Linktekst past bij doel (Joods Monument, Oorlogsbronnen e.d.)')
for p in paginas:
    for tekst, url in re.findall(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', p['body']):
        if not re.search(r'joodsmonument|oorlogsbronnen|oorlogsgravenstichting|wikipedia|stolpersteine', url): continue
        pad = urllib.parse.unquote(urllib.parse.urlparse(url).path).rstrip('/')
        slug = pad.rsplit('/', 1)[-1]
        if re.fullmatch(r'[0-9a-f-]{20,}', slug) or not re.search(r'[a-z]', slug): continue  # id zonder naam
        st, tt = tokens(slug.replace('_', ' ').replace('-', ' ')), tokens(re.sub(r'\\', '', tekst))
        if not st or not tt: continue
        if not (st & tt):
            meld(f'C! {p["slug"]}: linktekst "{tekst}" → {url}')
        elif len(st & tt) < min(len(st), len(tt)) and len(tt) >= 2 and len(st) >= 2 and not (tt <= st or st <= tt):
            meld(f'C? {p["slug"]}: gedeeltelijke overeenkomst "{tekst}" → {slug}')

# ---------- D: galerijen ----------
meld('\n=== D. Galerijfoto past bij de pagina waar hij naar linkt')
for naam in ('recent-gelegd', 'eerste'):
    p = per_slug[naam]
    items = re.findall(r'-\s*foto:\s*(\S+)\n((?:\s{4}\w+:.*\n)*)', p['fm'])
    for foto, rest in items:
        link = re.search(r'link:\s*"([^"]*)"', rest)
        alt = re.search(r'alt:\s*"([^"]*)"', rest)
        tekst = re.search(r'tekst:\s*"([^"]*)"', rest)
        if not link or not link.group(1).startswith('/'):
            meld(f'D- {naam}: {Path(foto).name} linkt extern of nergens heen ({link.group(1) if link else "-"})'); continue
        doel = per_slug.get(link.group(1).strip('/').split('/')[0].split('#')[0])
        if not doel: meld(f'D! {naam}: {Path(foto).name} → {link.group(1)} bestaat niet'); continue
        ft = tokens(Path(foto).stem + ' ' + (alt.group(1) if alt else ''))
        dt = tokens(paginatekst(doel))
        datum_ok = ''
        if tekst and doel['soort'] == 'adres':
            g = re.search(r'^gelegd:\s*(\S+)', doel['fm'], re.M)
            m = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{4})', tekst.group(1))
            if g and m and f'{int(m[3]):04d}-{int(m[2]):02d}-{int(m[1]):02d}' != g.group(1):
                datum_ok = f' | datum galerij "{tekst.group(1)}" ≠ gelegd {g.group(1)}'
        if not (ft & dt):
            meld(f'D! {naam}: foto "{Path(foto).name}" (alt "{alt.group(1) if alt else ""}") → {link.group(1)}: naam komt niet voor op die pagina{datum_ok}')
        elif datum_ok:
            meld(f'D? {naam}: {Path(foto).name} → {link.group(1)}{datum_ok}')

# ---------- E: overzichtstabel ----------
meld('\n=== E. Overzichtstabel (tot nu toe)')
ov = json.loads((WEB / 'src/data/overzicht.json').read_text(encoding='utf-8'))
for r in ov['rijen']:
    achter, voor, loc, gjm, ob, datum = (r + [{}] * 6)[:6]
    naam = f'{voor.get("tekst","")} {achter.get("tekst","")}'.strip()
    nt = tokens(naam, 3)
    # naam vs Joods Monument-link
    for cel, label in ((gjm, 'gjm'), (ob, 'oorlogsbronnen')):
        l = cel.get('link', '')
        if 'joodsmonument' in l:
            slug = urllib.parse.unquote(l.rstrip('/').rsplit('/', 1)[-1])
            st = tokens(slug.replace('-', ' '))
            if st and not (st & nt) and not re.search(r'\d', slug):
                meld(f'E! {naam}: {label}-link gaat naar "{slug}"')
            elif st and not (st & nt):
                meld(f'E- {naam}: {label}-link gaat naar adrespagina "{slug}" (geen persoon)')
    # locatie vs adreslink
    l = loc.get('link', '')
    if l.startswith('/'):
        slug = l.strip('/').split('/')[0]
        doel = per_slug.get(slug)
        if not doel: meld(f'E! {naam}: locatielink {l} bestaat niet'); continue
        lt, st = tokens(loc.get('tekst', '')), tokens(slug.replace('-', ' '))
        if not (lt & st): meld(f'E! {naam}: locatie "{loc.get("tekst")}" linkt naar {l}')
        if achter.get('tekst') and not (tokens(achter['tekst']) & tokens(paginatekst(doel))):
            meld(f'E? {naam}: achternaam niet gevonden op {l}')
        g = re.search(r'^gelegd:\s*(\S+)', doel['fm'], re.M)
        if g and re.fullmatch(r'\d{4}-\d{2}-\d{2}', datum.get('tekst', '')) and datum['tekst'] != g.group(1):
            meld(f'E? {naam}: datum tabel {datum["tekst"]} ≠ gelegd {g.group(1)} op {l}')

(ROOT / 'scripts/rapport-controle.txt').write_text('\n'.join(uit) + '\n', encoding='utf-8')
print('\n'.join(uit))
