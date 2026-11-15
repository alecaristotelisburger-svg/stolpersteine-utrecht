#!/usr/bin/env python3
"""Zet de adrespagina's uit de WordPress-back-up (html/) om naar
website/src/content/adressen/<slug>.md, met foto's in website/src/assets/adressen/.

Gebruik (vanuit de map van de back-up):
    python3 -I scripts/adressen_omzetten.py            # alles omzetten
    python3 -I scripts/adressen_omzetten.py slug ...   # alleen deze

- Tekst wordt letterlijk overgenomen (alleen opmaak wordt Markdown).
- Een standaardkop (aantal stenen / gelegd op / adres / voor:) gaat naar de
  gegevens bovenaan; afwijkende pagina's krijgen `eigen_opmaak: true` en worden
  in hun geheel als tekst overgenomen.
- Bestanden met `handmatig: true` in de gegevens worden niet overschreven.
- Coördinaten via PDOK Locatieserver (gemeente Utrecht).
Het script schrijft een rapport naar scripts/rapport-adressen.txt.
"""
import html as H, json, re, shutil, sys, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'website'
OUT = WEB / 'src/content/adressen'
ASSETS = WEB / 'src/assets/adressen'

SLUGS = """koekoekstraat-29b wittevrouwensingel-96d staalstraat-40 weerdsingel-oz-81b
schimmelpennicklaan-14 lombokstraat-18 franshalsstraat-19 willem-arntzskade-31-bs zaagmolenkade-38
justus-van-effenstraat-1 springweg-63 vrouwjuttenstraat-2 domstraat-31 vossegatsedijk-39
cartesiusweg-103 twijnstraat-16-bis koningsweg-111 havikstraat-18b sparstraat-59
nieuwe-koekoekstraat-81 adriaan-van-bergenstraat-123 mauritsstraat-105 bilderdijkstraat-15-bis
boomstraat-13 molierelaan-8 morelstraat-18 meerndijk-74 meerndijk-110 bijlhouwerstraat-6
kievitdwarsstraat-29 heijcopperkade-5-6 oudwijk-43 justus-van-effenstraat-13-13bis
stadhouderslaan-29 beverstraat-49 croeselaan-235 domplein-29 dieperinklaan-19 leliestraat-50-bis
voorstraat-1 ambachtstraat-2 kastanjestraat-6 nieuwe-gracht-92 julianaweg-22-utrecht
amsterdamsestraatweg-313 obrechtstraat-64""".split()

# Correcties op de bron, met reden (komen in het rapport).
TEKSTCORRECTIES = {
    'meerndijk-74': [('foto Doete Rechts', 'foto Doete Regts', 'spelfout fotografe')],
}
ADRES = {  # pagina's waar het adres niet als 'adres:'-regel in de tekst staat
    'nieuwe-gracht-92': 'Nieuwegracht 92',
    'amsterdamsestraatweg-313': 'Amsterdamsestraatweg 313',
}
ZOEK = {  # zoekterm voor PDOK als die afwijkt van het adres op de pagina
    'schimmelpennicklaan-14': 'Schimmelpennincklaan 14',
    'heijcopperkade-5-6': 'Heijcopperkade 6',
    'dieperinklaan-19': 'Prof. J.W. Dieperinklaan 19',
    'weerdsingel-oz-81b': 'Weerdsingel O.Z. 81',
}
ADRESCORRECTIES = {  # spelling van het adres (komt in het rapport)
    'schimmelpennicklaan-14': ('Schimmelpennicklaan', 'Schimmelpennincklaan'),
    'heijcopperkade-5-6': ('Heicopperkade', 'Heijcopperkade'),
    'willem-arntzskade-31-bs': ('Arntzskade', 'Arntszkade'),
}
# Blokken die per ongeluk van een andere pagina zijn meegekopieerd: vanaf deze tekst weglaten.
AFKAPPEN = {
    'meerndijk-110': ('adres : Molierelaan 8', 'kopie van de Molierelaan-pagina onder de eigen tekst'),
}

MAANDEN = {m: i + 1 for i, m in enumerate('januari februari maart april mei juni juli augustus september oktober november december'.split())}
BLOCK = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'figcaption', 'blockquote', 'td'}


# ---------- HTML → blokken ----------
def lees_blokken(src):
    a = src.find('data-elementor-type="wp-page"'); b = src.find('data-elementor-type="footer"')
    s = src[a:b]
    out = []

    class P(HTMLParser):
        def __init__(p):
            super().__init__(); p.cur = None; p.buf = ''; p.skip = 0; p.links = []; p.link_open = []
        def flush(p):
            if p.cur and p.buf.strip():
                out.append({'tag': p.cur, 'tekst': p.buf, 'links': p.links})
            p.cur = None; p.buf = ''; p.links = []
        def handle_starttag(p, t, a):
            a = dict(a)
            if t in ('script', 'style', 'svg', 'noscript'): p.skip += 1; return
            if p.skip: return
            if t in BLOCK:
                p.flush(); p.cur = t
            elif t == 'a':
                p.buf += '\x01'; p.links.append(a.get('href') or '')
            elif t == 'br': p.buf += '\n'
            elif t in ('em', 'i'): p.buf += '\x03'
            elif t == 'img':
                p.flush(); out.append({'tag': 'img', 'src': a.get('src'), 'alt': a.get('alt') or ''})
            elif t == 'iframe':
                src = a.get('src') or a.get('data-src') or a.get('data-lazy-load') or ''
                if src: p.flush(); out.append({'tag': 'video', 'src': src})
            elif t == 'div' and 'youtube' in (a.get('data-settings') or ''):
                m = re.search(r'"youtube_url":"([^"]+)"', H.unescape(a['data-settings']))
                if m: p.flush(); out.append({'tag': 'video', 'src': m.group(1).replace('\\/', '/')})
        def handle_endtag(p, t):
            if t in ('script', 'style', 'svg', 'noscript'): p.skip -= 1; return
            if p.skip: return
            if t == 'a': p.buf += '\x02'
            elif t in ('em', 'i'): p.buf += '\x03'
            elif t in BLOCK: p.flush()
        def handle_data(p, d):
            if not p.skip and p.cur: p.buf += d
    P().feed(s)
    for b in out:
        if 'tekst' in b:
            t = b['tekst'].replace('\xa0', ' ')
            t = re.sub(r'[ \t]+', ' ', t)
            t = '\n'.join(l.strip() for l in t.split('\n'))
            b['tekst'] = t.strip('\n ')
    # lege blokken (alleen opmaak/spaties) weg
    return [b for b in out if 'tekst' not in b or re.sub(r'[\x01\x02\x03\s]', '', b['tekst'])]


def platte_tekst(t):
    return re.sub(r'[\x01\x02\x03]', '', t).strip()


# ---------- kop herkennen ----------
DATUM = r'(\d{1,2})\s*[–-]?\s*(\d{1,2})\s*[–-]?\s*(\d{4})'
KOPREGELS = [
    r'(?P<n>\d+\s+)?Stolperstein(e)?( gelegd( op)?)?( ' + DATUM + r')?( voor\s*:)?',
    r'(gelegd )?op ' + DATUM + r'( voor\s*:)?',
    r'gelegd op ' + DATUM + r'( voor\s*:)?',
    DATUM,
    r'adres\s*:\s*.+',
    r'voor\s*:',
]


def is_kopregel(l):
    return any(re.fullmatch(p, l.strip(), flags=re.I) for p in KOPREGELS)


def parse_datum(t):
    m = re.search(DATUM, t)
    if m:
        d, mnd, j = map(int, m.groups())
        if 1 <= mnd <= 12 and 1 <= d <= 31: return f'{j:04d}-{mnd:02d}-{d:02d}'
    m = re.search(r'(\d{1,2}) (' + '|'.join(MAANDEN) + r') (\d{4})', t, re.I)
    if m: return f'{int(m.group(3)):04d}-{MAANDEN[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
    return None


# ---------- blokken → Markdown ----------
def esc(t):
    t = t.replace('\\', '\\\\')
    for c in '*_[]<>`':
        t = t.replace(c, '\\' + c)
    return t


WEGLINKS = {'/nog-niet-klaar/', '/vondellaan-24/'}  # gaan niet mee of bestaan niet (ook live 404): alleen de tekst blijft


def zet_link_om(url, rapport=None):
    """Google-doorverwijzing uitpakken, eigen site relatief maken, bijlagen meenemen."""
    url = url.strip()
    if re.match(r'https?://(www\.)?google\.[a-z.]+/url\?', url):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('q')
        if q: url = q[0]
    if re.match(r'https?:(%2F|/)', url) and '%2F' in url:  # nog gecodeerd
        url = urllib.parse.unquote(url)
    if url.count('http') > 1:  # dubbel geplakte URL: neem de laatste
        url = url[url.rfind('http'):]
    m = re.match(r'https?://(www\.)?stolpersteine-utrecht\.nl(/[^?#]*)?(.*)$', url)
    if not m: return url
    pad = m.group(2) or '/'
    if pad.startswith('/wp-content/uploads/'):
        bron = ROOT / 'media' / pad[len('/wp-content/uploads/'):]
        if bron.exists():
            doel = WEB / 'public' / pad.lstrip('/')
            doel.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(bron, doel)
        elif rapport is not None:
            rapport.append(f'  ! bijlage ontbreekt: {pad}')
        return pad
    if not pad.endswith('/') and '.' not in pad.rsplit('/', 1)[-1]: pad += '/'
    if pad in WEGLINKS:
        if rapport is not None: rapport.append(f'  ~ link naar {pad} weggehaald (pagina gaat niet mee)')
        return None
    return pad + m.group(3)


RAPPORT = []


def inline(b):
    """Tekst van een blok naar Markdown, met links en cursief."""
    links = iter(b['links']); res = ''; i = 0; t = b['tekst']
    parts = re.split(r'(\x01|\x02|\x03)', t)
    stack = []; ital = False
    for p in parts:
        if p == '\x01':
            stack.append((len(res), next(links, '')))
        elif p == '\x02':
            if stack:
                start, url = stack.pop(); txt = res[start:]
                lead = len(txt) - len(txt.lstrip()); trail = len(txt) - len(txt.rstrip())
                core = txt.strip()
                url = zet_link_om(url, RAPPORT) if url else None
                if url and core:
                    res = res[:start] + txt[:lead] + f'[{core}]({url.replace(" ", "%20")})' + (txt[len(txt) - trail:] if trail else '')
        elif p == '\x03':
            res += '\x03'
        else:
            res += esc(p)
    # cursief: paren van \x03 → *...* (spaties buiten de sterretjes)
    def ital_sub(m):
        inner = m.group(1)
        if not inner.strip(): return inner
        lead = inner[:len(inner) - len(inner.lstrip())]; trail = inner[len(inner.rstrip()):]
        return f'{lead}*{inner.strip()}*{trail}'
    res = re.sub(r'\x03([^\x03]*)\x03', ital_sub, res)
    res = res.replace('\x03', '')
    return res


KOPNIVEAU = {'h1': '##', 'h2': '###', 'h3': '###', 'h4': '###'}


def blok_md(b, slug, rapport, kopniveau=None, map_='adressen'):
    kopniveau = kopniveau or KOPNIVEAU
    if b['tag'] == 'img':
        pad = kopieer_media(b['src'], WEB / 'src/assets' / map_ / slug, rapport, voorkeur_origineel=True)
        if not pad: return None
        alt = b['alt'] or re.sub(r'[-_]+', ' ', pad.stem)  # zonder alt: naam uit bestandsnaam
        return f'![{esc(alt)}](../../assets/{map_}/{slug}/{pad.name})'
    if b['tag'] == 'video':
        vim = re.search(r'vimeo\.com/(?:video/)?(\d+)', b['src'])
        vid = re.search(r'(?:v=|youtu\.be/|/embed/)([\w-]{6,})', b['src'])
        if vim: src = f'https://player.vimeo.com/video/{vim.group(1)}?dnt=1'
        elif vid: src = f'https://www.youtube-nocookie.com/embed/{vid.group(1)}'
        else: rapport.append(f'  ! video niet herkend: {b["src"]}'); return None
        return f'<div class="video"><iframe src="{src}" title="Video" loading="lazy" allowfullscreen></iframe></div>'
    md = inline(b)
    regels = [r.strip() for r in md.split('\n')]
    regels = [r for r in regels if r]
    if not regels: return None
    tag = b['tag']
    if tag in ('h1', 'h2', 'h3', 'h4') and len(platte_tekst(b['tekst'])) > 120:
        tag = 'p'  # lange verhaaltekst die als kop was opgemaakt
    if tag in ('h1', 'h2', 'h3', 'h4'):
        niveau = kopniveau[tag]
        return f'{niveau} ' + '<br>'.join(regels)
    if tag == 'li':
        return '- ' + ' \\\n  '.join(regels)
    # alinea: begin niet met lijst/kop-tekens
    regels = [re.sub(r'^([-+#>]|\d+\.)(\s)', r'\\\1\2', r) for r in regels]
    return ' \\\n'.join(regels)


# ---------- media ----------
def lokaal(url):
    m = re.search(r'wp-content/uploads/(.+)$', url or '')
    return ROOT / 'media' / m.group(1) if m else None


def kopieer_media(url, doelmap, rapport, voorkeur_origineel=False, naam=None):
    p = lokaal(url)
    if not p: rapport.append(f'  ! geen lokale media voor {url}'); return None
    kand = []
    if voorkeur_origineel:
        basis = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', p.name)
        kand += [p.with_name(basis.replace('.', '-scaled.', 1)), p.with_name(basis)]
    kand.append(p)
    for k in kand:
        if k.exists():
            doelmap.mkdir(parents=True, exist_ok=True)
            doel = doelmap / (naam + k.suffix.lower() if naam else k.name.replace('-scaled', ''))
            shutil.copyfile(k, doel)
            return doel
    rapport.append(f'  ! bestand ontbreekt: {p}')
    return None


def achtergrondfoto(src):
    urls = re.findall(r'background-image:\s*url\(\s*["\']?([^"\')]+uploads/[^"\')]+)', src)
    urls = [u for u in urls if not re.search(r'servaas|raster|logo', u, re.I)]
    if not urls: return None
    # grootste variant: zonder -WxH
    urls.sort(key=lambda u: (bool(re.search(r'-\d+x\d+\.', u)), len(u)))
    return urls[0]


# ---------- coördinaten ----------
def pdok(adres):
    q = re.sub(r',?\s*(utrecht|de meern)\s*$', '', adres, flags=re.I)
    q = re.sub(r'\s+(bis|bs)\b', '', q, flags=re.I)
    q = re.sub(r'(\d)([A-Za-z])\b', r'\1 \2', q)
    url = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?' + urllib.parse.urlencode([
        ('q', q), ('fq', 'type:adres'), ('fq', 'gemeentenaam:Utrecht'), ('rows', '1'),
        ('fl', 'weergavenaam centroide_ll straatnaam huisnummer')])
    for poging in range(3):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=20))['response']['docs']
            break
        except Exception:
            time.sleep(2 * (poging + 1))
    else:
        return None
    if not d: return None
    d = d[0]
    norm = lambda s: re.sub(r'[^a-z]', '', s.lower().replace('é', 'e').replace('è', 'e').replace('ë', 'e'))
    straat = norm(re.sub(r'\d.*', '', q))
    gevonden = norm(d['straatnaam'])
    if not straat or not (gevonden == straat or gevonden.endswith(straat) or straat.endswith(gevonden)): return None
    huisnr = re.search(r'\d+', q)
    if not huisnr or str(d.get('huisnummer')) != huisnr.group(0): return None
    lng, lat = map(float, re.findall(r'[-\d.]+', d['centroide_ll']))
    return round(lat, 6), round(lng, 6), d['weergavenaam']


def kaartpunt(adres):
    norm = lambda t: re.sub(r'[^a-z0-9]', '', re.sub(r',.*$', '', t.lower()))
    data = json.loads((WEB / 'src/data/kaart-import.json').read_text(encoding='utf-8'))['punten']
    return next((p for p in data if norm(p['adres']) == norm(adres) and 'geocode' not in p), None)


# ---------- één pagina ----------
def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def omzetten(slug, rapport):
    bestand = next((ROOT / 'html').glob(f'page-*-{slug}.html'))
    doel = OUT / f'{slug}.md'
    if doel.exists() and 'handmatig: true' in doel.read_text(encoding='utf-8').split('---')[1]:
        rapport.append(f'= {slug}: handmatig bestand, overgeslagen'); return
    src = bestand.read_text(encoding='utf-8')
    for oud, nieuw, reden in TEKSTCORRECTIES.get(slug, []):
        if oud in src:
            src = src.replace(oud, nieuw); rapport.append(f'  ~ correctie: "{oud}" → "{nieuw}" ({reden})')
    blokken = lees_blokken(src)
    if slug in AFKAPPEN:
        tekst, reden = AFKAPPEN[slug]
        idx = next((i for i, b in enumerate(blokken) if tekst in platte_tekst(b.get('tekst', ''))), None)
        if idx is not None:
            # neem ook de kopregels vlak ervoor mee
            while idx > 0 and is_kopregel(platte_tekst(blokken[idx - 1].get('tekst', 'x'))) : idx -= 1
            weg = blokken[idx:]; blokken = blokken[:idx]
            rapport.append(f'  ~ weggelaten ({reden}): ' + ' | '.join(platte_tekst(b.get('tekst', '')) for b in weg))

    # fotovermelding (staat vóór de kop)
    credit = []
    while blokken and 'tekst' in blokken[0] and re.fullmatch(r'(foto\s*)?(Doete \w+)?', platte_tekst(blokken[0]['tekst']), re.I) and platte_tekst(blokken[0]['tekst']):
        credit.append(platte_tekst(blokken.pop(0)['tekst']))

    # video/afbeelding vóór de kop: blijft bovenaan de tekst
    voor_kop = []
    while blokken and 'tekst' not in blokken[0]:
        voor_kop.append(blokken.pop(0))

    # standaardkop?
    kop = []; i = 0
    while i < len(blokken) and 'tekst' in blokken[i] and not blokken[i]['links']:
        regels = [l for l in platte_tekst(blokken[i]['tekst']).split('\n') if l.strip()]
        if regels and all(is_kopregel(l) for l in regels):
            kop += regels; i += 1
        else:
            break
    kop_tekst = ' '.join(kop)
    adres_m = re.search(r'adres\s*:\s*(.+?)$', '\n'.join(kop), re.I | re.M)
    eigen = not (adres_m and parse_datum(kop_tekst))
    if eigen:
        kop = []; i = 0
    rest = voor_kop + blokken[i:]

    meta = {'slug': slug}
    if adres_m and not eigen:
        meta['adres'] = adres_m.group(1).strip()
    else:
        # adres uit de tekst of uit de slug
        alle = '\n'.join(platte_tekst(b.get('tekst', '')) for b in blokken)
        m = re.search(r'adres\s*:\s*(.+?)$', alle, re.I | re.M)
        meta['adres'] = ADRES.get(slug) or (m.group(1).strip() if m else slug.replace('-', ' ').title())
    n = re.search(r'(\d+)\s+Stolperstein', kop_tekst)
    if n: meta['aantal_stenen'] = int(n.group(1))
    elif re.search(r'\bStolperstein\b(?!e)', kop_tekst): meta['aantal_stenen'] = 1
    datum = parse_datum(kop_tekst) or parse_datum('\n'.join(platte_tekst(b.get('tekst', '')) for b in blokken[:3]))
    if datum: meta['gelegd'] = datum
    meta['voor'] = bool(re.search(r'voor\s*:', kop_tekst, re.I))
    if eigen: meta['eigen_opmaak'] = True

    if slug in ADRESCORRECTIES:
        oud, nieuw = ADRESCORRECTIES[slug]
        meta['adres'] = meta['adres'].replace(oud, nieuw); rapport.append(f'  ~ adres: "{oud}" → "{nieuw}"')
    geo = pdok(ZOEK.get(slug, meta['adres'])); time.sleep(0.3)
    if geo:
        meta['lat'], meta['lng'] = geo[0], geo[1]; meta['geocode'] = 'PDOK: ' + geo[2]
    else:
        k = kaartpunt(meta['adres'])
        if k:
            meta['lat'], meta['lng'] = k['lat'], k['lng']; meta['geocode'] = 'oude Google-kaart: ' + k['adres']
            rapport.append(f'  ~ coördinaten uit oude Google-kaart ({k["adres"]})')
        else:
            rapport.append(f'  ! geen coördinaten gevonden voor "{meta["adres"]}"')

    bg = achtergrondfoto(src)
    if bg:
        f = kopieer_media(bg, ASSETS, rapport, voorkeur_origineel=True, naam=f'{slug}-legging')
        if f: meta['foto'] = f'../../assets/adressen/{f.name}'; meta['foto_bron'] = bg.split('uploads/')[1]
    if credit: meta['foto_credit'] = ' '.join(credit)

    body = []
    for b in rest:
        m = blok_md(b, slug, rapport)
        if not m: continue
        # opeenvolgende afbeeldingen in één alinea: ze staan dan naast elkaar (zoals in de bron)
        if m.startswith('![') and body and body[-1].startswith('!['):
            body[-1] += ' ' + m
        else:
            body.append(m)
    meta['bron'] = f'html/{bestand.name}'

    fm = ['---', f'adres: {yaml_str(meta["adres"])}', f'slug: {slug}']
    if 'aantal_stenen' in meta: fm.append(f'aantal_stenen: {meta["aantal_stenen"]}')
    if 'gelegd' in meta: fm.append(f'gelegd: {meta["gelegd"]}')
    if meta.get('voor'): fm.append('voor: true')
    if eigen: fm.append('eigen_opmaak: true')
    if 'lat' in meta: fm += [f'lat: {meta["lat"]}', f'lng: {meta["lng"]}', f'geocode: {yaml_str(meta["geocode"])}']
    if 'foto' in meta: fm += [f'foto: {meta["foto"]}']
    if 'foto_credit' in meta: fm.append(f'foto_credit: {yaml_str(meta["foto_credit"])}')
    fm += [f'bron: {meta["bron"]}', '---', '']
    doel.write_text('\n'.join(fm) + '\n\n'.join(body) + '\n', encoding='utf-8')

    rapport.append(f'+ {slug}: adres="{meta["adres"]}" gelegd={meta.get("gelegd")} stenen={meta.get("aantal_stenen")} '
                   f'{"EIGEN OPMAAK " if eigen else ""}foto={"ja" if "foto" in meta else "nee"} '
                   f'kop=[{" / ".join(kop)}]')

    # controle: komt elk woord uit de bron terug?
    woorden = lambda t: set(re.findall(r'\w+', t.lower()))
    bronw = set().union(set(), *[woorden(platte_tekst(b.get('tekst', ''))) for b in rest]) | woorden(' '.join(credit))
    uitw = woorden(doel.read_text(encoding='utf-8').replace('\\', ''))
    mist = bronw - uitw
    if mist: rapport.append(f'  ! woorden niet in uitvoer: {sorted(mist)}')


if __name__ == '__main__':
    if '--forceer' not in sys.argv:
        sys.exit('Let op: de pagina\'s zijn na het omzetten met de hand aangepast (menu 13-11-2026).\n'
                 'Opnieuw omzetten overschrijft die wijzigingen. Toch doorgaan: voeg --forceer toe.')
    sys.argv = [a for a in sys.argv if a != '--forceer']
    OUT.mkdir(parents=True, exist_ok=True)
    rapport = RAPPORT
    for s in (sys.argv[1:] or SLUGS):
        omzetten(s, rapport)
    (ROOT / 'scripts/rapport-adressen.txt').write_text('\n'.join(rapport) + '\n', encoding='utf-8')
    print('\n'.join(rapport))
