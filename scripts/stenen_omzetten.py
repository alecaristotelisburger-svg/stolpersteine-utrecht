#!/usr/bin/env python3
"""Eenmalig: zet de tabel src/data/overzicht.json (uit Ninja Tables) om naar
één JSON-bestand per steen in website/src/content/stenen/. Daarna wordt de
tabel beheerd via de back-office (/admin/) en is overzicht.json alleen archief.

    python3 -I scripts/stenen_omzetten.py --forceer
"""
import json, re, sys, unicodedata
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / 'website'
UIT = WEB / 'src/content/stenen'

if '--forceer' not in sys.argv:
    sys.exit('Dit overschrijft src/content/stenen/ (ook wijzigingen uit de back-office). Toch doorgaan: --forceer')

def slugify(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

d = json.loads((WEB / 'src/data/overzicht.json').read_text(encoding='utf-8'))
adressen = {p.stem for p in (WEB / 'src/content/adressen').glob('*.md')}
paginas = {p.stem for p in (WEB / 'src/content/paginas').glob('*.md')}
def fm(p, k):
    m = re.search(rf'^{k}:\s*"?([^"\n]*)"?', p.read_text(encoding='utf-8').split('---')[1], re.M)
    return m.group(1).strip() if m else ''
def kort(t):  # "Frans Halsstraat 44 Utrecht" / "Frans Halsstraat 44, 3583 BK, Utrecht" -> "franshalsstraat44"
    t = re.split(r',', t)[0]
    t = re.sub(r'\b(utrecht|de meern)\b', '', t, flags=re.I)
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower())
adres_op_kort = {kort(fm(p, 'adres')): p.stem for p in (WEB / 'src/content/adressen').glob('*.md')}
persoon_op_naam = {}
for p in (WEB / 'src/content/paginas').glob('*.md'):
    if fm(p, 'soort') == 'persoon':
        persoon_op_naam[re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', fm(p, 'titel')).encode('ascii', 'ignore').decode().lower())] = p.stem
tel = {'adres (link)': 0, 'adres (op adres)': 0, 'persoon (op naam)': 0}
UIT.mkdir(parents=True, exist_ok=True)
for f in UIT.glob('*.json'): f.unlink()

gezien = set()
for r in d['rijen']:
    achter, voor, loc, gjm, gob, datum = r
    s = {
        'achternaam': achter['tekst'].strip(),
        'voornaam': voor['tekst'].strip(),
        'locatie': loc['tekst'].strip(),
    }
    link = loc.get('link', '')
    if link.startswith('/'):
        slug = link.strip('/').split('/')[0]
        if slug in adressen: s['adrespagina'] = slug; tel['adres (link)'] += 1
        elif slug in paginas: s['persoonspagina'] = slug
    elif link:
        s['locatie_link'] = link.replace('%2F', '/')
    if 'adrespagina' not in s and adres_op_kort.get(kort(s['locatie'])):
        s['adrespagina'] = adres_op_kort[kort(s['locatie'])]; tel['adres (op adres)'] += 1
    vol = re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', f"{s['voornaam']}{s['achternaam']}").encode('ascii', 'ignore').decode().lower())
    if vol in persoon_op_naam:
        s['persoonspagina'] = persoon_op_naam[vol]; tel['persoon (op naam)'] += 1
    if gjm.get('link'): s['joodsmonument'] = gjm['link']
    if gob.get('link'): s['oorlogsbronnen'] = gob['link']
    t = datum['tekst'].strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', t):
        s['status'] = 'gelegd'; s['gelegd'] = t
    else:
        s['status'] = 'nog niet geplaatst'
    naam = slugify(f"{s['achternaam']} {s['voornaam']}") or 'steen'
    n, i = naam, 2
    while n in gezien: n, i = f'{naam}-{i}', i + 1
    gezien.add(n)
    (UIT / f'{n}.json').write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(len(gezien), 'stenen geschreven naar', UIT, tel)
