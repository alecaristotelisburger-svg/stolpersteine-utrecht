#!/usr/bin/env python3
"""Zet de overige WordPress-pagina's (informatie, personen, video's) om naar
website/src/content/paginas/<slug>.md. Tekst letterlijk; galerijen en
diavoorstellingen gaan naar `galerij:` in de gegevens.

Gebruik (vanuit de map van de back-up):
    python3 -I scripts/paginas_omzetten.py            # alles
    python3 -I scripts/paginas_omzetten.py slug ...   # alleen deze

Maakt ook website/src/data/overzicht.json (de tabel van /locatie-volgens-sheets/).
Rapport: scripts/rapport-paginas.txt
"""
import html as H, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adressen_omzetten as A  # noqa: E402

ROOT, WEB = A.ROOT, A.WEB
OUT = WEB / 'src/content/paginas'
PAGES = {p['post_name']: p for p in json.loads((ROOT / 'content/page.json').read_text(encoding='utf-8'))}
MEDIA = json.loads((ROOT / 'content/media.json').read_text(encoding='utf-8'))

PERSONEN = """ester-sara-choczner salomon-choczner-2 mechel-rechter bernard-rechter-2 beila-kluger dora-pawliger
ludwig-f-simon raphael-wrazlowskij derkje-van-lier josephina-joosten-groen kurt-adolf-roeders antoinette-roeders
liselotte-selinko bernard-hes sonja-jacoba-hes jacobus-lambertus-hordijk helena-v-staveren wijnschenk-israel
wijnschenk-kitty wilhelmus-wilschut roosje-van-der-sluijs lea-van-der-sluijs eliazer-horneman
jeannetta-horneman-leviticus saartje-horneman-kaufman izaak-horneman meijerson-arnold-lucien
meijerson-alfred-jacques hortense-evaline-meijerson johanna-rosalia-meijerson-cohen straus-joseph straus-barend""".split()
VIDEO = """here-lived-trailer stolpersteine-the-worlds-largest-memorial westerbork-materiaal als-of-wij-drieen
drie-meisjes over-nic-jesse mieks-snackers cohen 3-2""".split()
INFO = """aanvragen bronnen-voor-onderzoek colofon contact educatie eerste gelegd gezocht in-de-media
komende-leggingen laatste-nieuws lesmateriaal missie netwerk-bijeenkomst-2023 nieuws over-ons recent-gelegd
steun-ons stolpersteine-in-utrecht uit-de-gemeenteraad utrecht-1942 voor-wie voorbeeld wat-zijn
potentiele-adressen""".split()
CONCEPT = {'potentiele-adressen'}  # wordt omgezet maar niet gepubliceerd
# Afbeeldingen die niet meegaan (geen inhoud)
WEG_AFBEELDINGEN = re.compile(r'SeekPng|submit-spin|profile-icon', re.I)
# Blokken die weg moeten, met reden
WEG_BLOKKEN = {
    'contact': [(r'^U kunt onderstaand contact-formulier gebruiken', 'het formulier (WPForms) gaat niet mee; contact via e-mail')],
}
TITEL = {'contact': 'Contact'}  # vaste kop; de eerste kop blijft dan in de tekst
KOPNIVEAU = {'h1': '##', 'h2': '##', 'h3': '###', 'h4': '###'}


def media_titel(url):
    naam = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', url.rsplit('/', 1)[-1]).replace('-scaled', '')
    stam = naam.rsplit('.', 1)[0]
    for m in MEDIA:
        if m.get('link', '').rsplit('/', 1)[-1].startswith(stam):
            return m.get('alt') or m.get('title') or ''
    return ''


def galerij_items(src, slug, rapport):
    a = src.find('data-elementor-type="wp-page"'); b = src.find('data-elementor-type="footer"'); m = src[a:b]
    items = []
    # Elementor-galerij
    links = []
    lm = re.search(r'var links = \[(.*?)\];', m, re.S)
    if lm: links = re.findall(r"'([^']*)'", lm.group(1))
    for i, it in enumerate(re.finditer(r'<(a|div) class="e-gallery-item[^"]*"([^>]*)>(.*?)</\1>\s*(?=<(?:a|div) class="e-gallery-item|</div>\s*</div>)', m, re.S)):
        attrs, inner = it.group(2), it.group(3)
        thumb = re.search(r'data-thumbnail="([^"]+)"', inner)
        if not thumb: continue
        href = re.search(r'href="([^"]+)"', attrs)
        link = links[i] if i < len(links) and len(links[i]) > 4 else (href.group(1) if href and not re.search(r'\.(jpe?g|png|webp)$', href.group(1), re.I) else '')
        titel = re.search(r'elementor-gallery-item__title">\s*([^<]*?)\s*<', inner)
        besch = re.search(r'elementor-gallery-item__description">\s*([^<]*?)\s*<', inner)
        items.append({'url': H.unescape(thumb.group(1)), 'tekst': ' '.join(x for x in [titel and titel.group(1), besch and besch.group(1)] if x),
                      'link': A.zet_link_om(H.unescape(link), rapport) if link else ''})
    # Diavoorstelling (slides): achtergrondfoto per dia + kop
    if 'slides.default' in m:
        fotos = re.findall(r'elementor-repeater-item-\w+ \.swiper-slide-bg\{[^}]*background-image:url\(([^)]+)\)', src)
        koppen = re.findall(r'class="swiper-slide-heading"[^>]*>([^<]*)<', m) or re.findall(r'<h4[^>]*>([^<]*)</h4>', m)
        for i, f in enumerate(fotos):
            items.append({'url': f, 'tekst': H.unescape(koppen[i]).strip() if i < len(koppen) else '', 'link': '', 'dia': True})
    # kopiëren
    uit = []
    for n, it in enumerate(items):
        pad = A.kopieer_media(it['url'], WEB / 'src/assets/paginas' / slug, rapport, voorkeur_origineel=True)
        if not pad: continue
        uit.append({'foto': f'../../assets/paginas/{slug}/{pad.name}', 'alt': media_titel(it['url']),
                    'tekst': it['tekst'], 'link': it['link'] or ''})
    return uit, [it['tekst'] for it in items if it.get('dia')]


def omzetten(slug, soort, rapport):
    bestand = next((ROOT / 'html').glob(f'page-*-{slug}.html'))
    src = bestand.read_text(encoding='utf-8')
    blokken = A.lees_blokken(src)
    galerij, diakoppen = galerij_items(src, slug, rapport)
    # koppen van de diavoorstelling staan al in de galerij
    blokken = [b for b in blokken if not ('tekst' in b and b['tag'] == 'h4' and A.platte_tekst(b['tekst']) in diakoppen)]
    blokken = [b for b in blokken if not (b['tag'] == 'img' and WEG_AFBEELDINGEN.search(b.get('src') or ''))]
    for patroon, reden in WEG_BLOKKEN.get(slug, []):
        weg = [b for b in blokken if 'tekst' in b and re.search(patroon, A.platte_tekst(b['tekst']))]
        for b in weg: rapport.append(f'  ~ weggelaten ({reden}): {A.platte_tekst(b["tekst"])[:80]}')
        blokken = [b for b in blokken if b not in weg]

    # kop (h1)
    titel = TITEL.get(slug)
    if titel:
        pass
    elif soort == 'persoon':
        for b in blokken:
            m = re.search(r'Voor\s*:\s*(.+)', A.platte_tekst(b.get('tekst', '')), re.I)
            if m and m.group(1).strip():
                titel = m.group(1).strip(); break
    else:
        eerste = next((i for i, b in enumerate(blokken) if 'tekst' in b), None)
        if eerste is not None and blokken[eerste]['tag'] in ('h1', 'h2', 'h3') and not blokken[eerste]['links']:
            t = A.platte_tekst(blokken[eerste]['tekst'])
            if 0 < len(t) < 80 and '\n' not in t:
                titel = t; blokken.pop(eerste)
    if not titel:
        t = H.unescape(PAGES[slug]['post_title'])
        titel = t[:1].upper() + t[1:]
        rapport.append(f'  ~ kop uit paginatitel: "{titel}"')

    body = []
    for b in blokken:
        md = A.blok_md(b, slug, rapport, kopniveau=KOPNIVEAU, map_='paginas')
        if not md: continue
        if md.startswith('![') and body and body[-1].startswith('!['):
            body[-1] += ' ' + md
        else:
            body.append(md)

    # e-mailadressen klikbaar maken
    body = [re.sub(r'(?<![\[(\w.:/])([\w.+-]+@[\w-]+\.[a-z]{2,})(?![\w\]])', r'[\1](mailto:\1)', md) for md in body]

    fm = ['---', f'titel: {A.yaml_str(titel)}', f'slug: {slug}', f'soort: {soort}']
    if slug in CONCEPT: fm.append('concept: true  # niet publiceren zonder controle')
    bg = A.achtergrondfoto(src)
    if bg:
        f = A.kopieer_media(bg, WEB / 'src/assets/paginas', rapport, voorkeur_origineel=True, naam=f'{slug}-achtergrond')
        if f: fm.append(f'foto: ../../assets/paginas/{f.name}')
    if galerij:
        fm.append('galerij:')
        for g in galerij:
            fm.append(f'  - foto: {g["foto"]}')
            for k in ('alt', 'tekst', 'link'):
                if g[k]: fm.append(f'    {k}: {A.yaml_str(g[k])}')
    fm += [f'bron: html/{bestand.name}', '---', '']
    doel = OUT / f'{slug}.md'
    doel.write_text('\n'.join(fm) + '\n\n'.join(body) + '\n', encoding='utf-8')
    rapport.append(f'+ {slug} ({soort}): kop="{titel}" blokken={len(body)} galerij={len(galerij)} achtergrond={"ja" if bg else "nee"}')

    woorden = lambda t: set(re.findall(r'\w+', t.lower()))
    bronw = set().union(set(), *[woorden(A.platte_tekst(b.get('tekst', ''))) for b in blokken]) | woorden(titel)
    mist = bronw - woorden(doel.read_text(encoding='utf-8').replace('\\', ''))
    if mist: rapport.append(f'  ! woorden niet in uitvoer: {sorted(mist)}')


def overzicht(rapport):
    """De Ninja Tables-tabel van /locatie-volgens-sheets/ als JSON."""
    src = next((ROOT / 'html').glob('page-*-locatie-volgens-sheets.html')).read_text(encoding='utf-8')
    label = re.search(r'<table[^>]*aria-label="([^"]*)"', src)
    koppen = [H.unescape(k).strip() for k in re.findall(r'<th[^>]*>([^<]*)</th>', src)]
    rijen = []
    for r in re.findall(r'<tr data-row_id.*?</tr>', src, re.S):
        cellen = re.findall(r'<td>(.*?)</td>', r, re.S)
        rij = []
        for c in cellen:
            a = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', c, re.S)
            tekst = H.unescape(re.sub(r'<[^>]+>', '', a.group(2) if a else c)).strip()
            link = A.zet_link_om(H.unescape(a.group(1)), rapport) if a else ''
            rij.append({'tekst': tekst, 'link': link} if link else {'tekst': tekst})
        rijen.append(rij)
    # laatste kolom ('uitgelicht') is op de oude site verborgen
    verborgen = [i for i, k in enumerate(re.findall(r'<th[^>]*class="([^"]*)"', src)) if 'hidden' in k]
    koppen = [k for i, k in enumerate(koppen) if i not in verborgen]
    rijen = [[c for i, c in enumerate(r) if i not in verborgen] for r in rijen]
    data = {'titel': H.unescape(label.group(1)) if label else '', 'kolommen': koppen, 'rijen': rijen}
    (WEB / 'src/data/overzicht.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    rapport.append(f'+ overzicht.json: {len(rijen)} rijen, kolommen {koppen}')


if __name__ == '__main__':
    if '--forceer' not in sys.argv:
        sys.exit('Let op: de pagina\'s zijn na het omzetten met de hand aangepast en samengevoegd (menu 13-11-2026).\n'
                 'Opnieuw omzetten overschrijft die wijzigingen. Toch doorgaan: voeg --forceer toe.')
    sys.argv = [a for a in sys.argv if a != '--forceer']
    OUT.mkdir(parents=True, exist_ok=True)
    rapport = A.RAPPORT
    soorten = {**{s: 'persoon' for s in PERSONEN}, **{s: 'video' for s in VIDEO}, **{s: 'info' for s in INFO}}
    for s in (sys.argv[1:] or soorten):
        omzetten(s, soorten[s], rapport)
    if not sys.argv[1:]: overzicht(rapport)
    (ROOT / 'scripts/rapport-paginas.txt').write_text('\n'.join(rapport) + '\n', encoding='utf-8')
    print('\n'.join(rapport))
