# Stolpersteine Utrecht — website

Context voor Claude. Communiceer met de gebruiker in het **Nederlands**.

## Doel

De gebruiker (beheerder van stolpersteine-utrecht.nl, Stichting Stolpersteine Utrecht) wil **weg van WordPress** en de site omzetten naar een **statische website** die volledig in eigen beheer is: bestanden in een GitHub-repository, bewerkt met hulp van Claude. Deze map is de back-up die als bron dient voor die overstap.

Eerder is ook overwogen om de WordPress-site eerst op te schonen. Dat is niet meer het hoofddoel, maar de analyse hieronder blijft nuttig.

## Inhoud van deze map

Back-up van 13 november 2026. Zie `LEESMIJ.txt` en `MANIFEST.json`.

- `content/` — JSON via XML-RPC: `page.json` (125 pagina's: 123 gepubliceerd en 2 concepten, met `post_content`, slug, datums en custom fields zoals Yoast-meta), `media.json` (432 items), Elementor-sjablonen (`elementor_library.json`), header/footer (`elementor-hf.json`), menu's en opties.
- `html/` — gerenderde HTML van elke gepubliceerde pagina, als `<type>-<id>-<slug>.html`. **Dit is de betrouwbaarste bron voor inhoud en opbouw**, omdat `post_content` van Elementor-pagina's vaak leeg of rommelig is.
- `media/` — volledige `wp-content/uploads` (originelen, gebruikte formaten, Elementor-css en lettertypen).
- `assets/` — CSS, JS, lettertypen en iconen van thema en plugins, voor het nabouwen van de vormgeving.
- `site/` — `robots.txt` en sitemaps: de lijst van alle openbare URL's.

**Ontbreekt:** Elementor-opmaakdata (`_elementor_data` geeft XML-RPC niet vrij), plugin- en thema-instellingen, gebruikers en de database.

Inhoud van de HTML: pak het deel tussen `data-elementor-type="wp-page"` en `data-elementor-type="footer"`. Header en footer zijn op alle pagina's gelijk.

## De huidige site

- WordPress 7.1 op **Elementor Cloud** (beheer via my.elementor.com, met back-ups en mogelijk staging). Achter Cloudflare.
- De domeinnaam is geregistreerd bij een aparte webhost. Bij de overstap verandert alleen de DNS.
- Thema Astra, Elementor + Elementor Pro, Header Footer Elementor voor header en footer.
- Uitstraling (gemeten op de live site, 13-11-2026): **donker**. Achtergrond `#202819`, menubalk en footer `#314336`, submenu `#54715e` met gele links, geel `#ffd936` voor links, knoppen als pil in olijf `#c1b92f`, witte tekst. Actief menu-item `#61ce70`. Overal DM Sans (Forum wordt niet zichtbaar gebruikt). Homepagefoto met laag `rgb(94 118 101 / .5)`. Adrespagina's hebben een foto van de legging als achtergrond met laag `#324336` (45%). Logo: raster van 3×3 grijze tegels met één gele. Deze waarden staan in `website/src/styles/huisstijl.css`.
- Menu (live): Stolpersteine in Utrecht (wat zijn, voor wie, gelegd › [recent gelegd, eerste, tot nu toe = `/locatie-volgens-sheets/`], waar = `/maps/`, aanvragen, komende leggingen) · educatie (lesmateriaal, voorbeelden = `/voorbeeld/`, Utrecht 1942) · nieuws (in de media, uit de gemeenteraad) · gezocht. Plus een zoekbalk.

### Pagina's (stand 13-11-2026)

- **Menu- en informatiepagina's** (~27): zie het menu hierboven, plus steun ons, over ons, contact, missie, colofon, bronnen voor onderzoek, laatste nieuws, netwerk bijeenkomst 2023.
- **Adrespagina's** (~46, het nieuwe model sinds eind 2024): één pagina per adres met alle personen die er woonden. Vaste opbouw: aantal stenen, adres, "gelegd op <datum> voor:", namen (h1), verhaal en foto.
- **Persoonspagina's** (32, het oude model 2023–2024): één pagina per persoon.
- **Video's en achtergrond** (~9): here lived trailer, worlds largest memorial, westerbork materiaal, als of wij drieen, drie meisjes, over nic jesse, mieks snackers, cohen, `/3-2/` (foto Joodse School).
- **Test- en werkpagina's, niet meenemen zonder overleg:** Elementor #14576, youtube test, tablepress tabel, ninja tabel pro, nog niet klaar (wel gelinkt vanaf 3 Horneman-persoonspagina's), nieuwe pagina voor ??, nieuwe map, "recent gelegd - Dupliceren", concepten Elementor #13829 en #14823.
- `/locatie-volgens-sheets/` (Ninja Tables, data uit een Google Sheet) is **de enige pagina die naar alle adres- en persoonspagina's linkt**. Het is dus een echte pagina, geen test.

### Gevoelig

- **`/potentiele-adressen/`**: kan adressen bevatten waar nog geen steen ligt. Niet openbaar publiceren zonder dat de gebruiker het heeft bekeken.
- Het gaat om namen, geboortedata en levensverhalen van slachtoffers. Neem tekst **letterlijk** over en verzin niets. Laat de omgezette pagina's door een mens controleren.

## Analyse van de oude site (oktober 2026)

- Homepage: ca. 1,5 KB zichtbare tekst, maar 3,6 MB geladen, 47 CSS- en 33 JS-bestanden. Slechts **5% van de CSS** wordt gebruikt.
- CSS van de blokeditor (~600 KB) laadt aan de voorkant, door EmbedPress en BetterDocs. Font Awesome laadt 2 tot 3 keer. Er zijn 6 lettertypefamilies, terwijl er 2 zichtbaar zijn.
- Contactformulier is **WPForms**. Contact Form 7 + Extensions for CF7 laden overal maar worden nergens gebruikt.
- Ongebruikt: TablePress, EmbedPress (+Pro), Document Embedder, BetterDocs. Bijna ongebruikt: Premium Addons (+Pro, alleen Ken Burns op /voor-wie), Essential Addons (datatabel op /komende-leggingen), Responsive Lightbox (alleen /3-2/), Ninja Tables (alleen locatie-volgens-sheets en een testpagina).
- Achtergrondfoto homepage `2026/10/servaasbolwerk-blurred.jpg` is 725 KB (2560×1153).
- Koppen kloppen niet: homepage heeft 4 `<h1>`'s, veel pagina's hebben er geen. Er zijn veel lege koppen.
- Privacy: Google Analytics (Site Kit) laadt vóór toestemming. Google Fonts komen extern. De cookiebanner (CookieYes) is in het Engels.

## Plan voor de nieuwe site

Voorgesteld, nog niet besloten:

- Statische sitegenerator (bijvoorbeeld Astro of Eleventy) in een GitHub-repository, gehost op Cloudflare Pages, Netlify of GitHub Pages (gratis).
- **Behoud dezelfde URL's** (slugs uit de sitemap) of maak redirects.
- Adressen en personen als **gestructureerde data** (één bestand per adres). Daaruit worden de adrespagina's, het overzicht (vervanger van locatie-volgens-sheets) en een kaart (Leaflet + OpenStreetMap) gegenereerd.
- Zoeken met Pagefind. Contact via een formulierdienst (bijvoorbeeld Formspree) of e-mail. YouTube via `youtube-nocookie`. Geen tracking of een privacyvriendelijke teller, zodat er geen cookiebanner nodig is.
- Afbeeldingen verkleinen en omzetten naar WebP. Eén `<h1>` per pagina.
- Stappen:
  1. Proefversie (homepage, één adrespagina, kaart).
  2. Alle inhoud omzetten.
  3. Menselijke controle.
  4. Proefdraaien op een tijdelijk adres naast WordPress.
  5. DNS omzetten en pas daarna Elementor Cloud opzeggen.

## Nieuwe site: `website/` (Astro 7, gestart 13-11-2026)

### Menu en indeling (besloten door gebruiker, 13-11-2026)
- **De Stolpersteine** `/stolpersteine-in-utrecht/` (tekst van "wat zijn") → Komende leggingen `/komende-leggingen/` · Gelegde Stolpersteine `/gelegd/` · Potentiële adressen `/potentiele-adressen/` · Aanvragen `/aanvragen/`
- **Organisatie** `/organisatie/` → Over dit initiatief `/over-ons/` (incl. missie) · Voor wie · Steun ons
- **Educatie** `/educatie/` → Lesmateriaal `/lesmateriaal/` (incl. voorbeelden) · Utrecht in de oorlog `/utrecht-in-de-oorlog/` (wordt nieuw; nu nog de tekst van Utrecht 1942) · Op TV en internationaal `/op-tv-en-internationaal/`
- **Nieuws** `/nieuws/`: artikelen (paginas met `soort: artikel` + `datum`, nieuwste eerst) en daaronder "In de media". **Vrijwilligers Gezocht** `/gezocht/`.
- `/gelegd/` = `src/pages/gelegd.astro`: kaart (`components/Kaart.astro`, ondergrond PDOK BRT-achtergrondkaart 'grijs': geen POI's, geen sleutel; CARTO vraagt sinds kort een API-sleutel), strook recent gelegd (8 foto's), blok "De eerste", lijst (`components/Overzicht.astro`). Kaart op adres: `/gelegd/?adres=<slug>#kaart`.
- `/op-tv-en-internationaal/` toont de losse video-pagina's (lijst `SLUGS` in het bestand).
- Footer: Contact (stolpersteine.utrecht@gmail.com) en een knop "Steun ons" (lichtmessing), Admin-knop, plus "© Stolpersteine Utrecht {jaar}" (`copyright` in `site.json`; `{jaar}` = huidig jaar, bij build ingevuld en in de browser bijgewerkt). Menu en footer in `src/data/site.json`.
- Samengevoegd/hernoemd, met doorverwijzing in `astro.config.mjs`: maps, locatie-volgens-sheets, wat-zijn, missie, colofon (weg: "tekst volgt"), bronnen-voor-onderzoek (nu onderaan Potentiële adressen), voorbeeld, utrecht-1942, in-de-media, laatste-nieuws (gelijk aan netwerk-bijeenkomst-2023).
- `/potentiele-adressen/` is gepubliceerd: het bleek een handleiding zonder adressen.
- Inhoudscontrole (13-11-2026): `scripts/controleer_inhoud.py` (foto's vs bron, linktekst vs doel, galerijen, tabel). Bevindingen en open punten: `CONTROLE-personen-13112026.md`. Havikstraat 18B is nu `handmatig: true` (Marcus Weisz-link hersteld).
- **Huisstijl nieuwe site** (gekozen 13-11-2026, variant C "gedenkboek", minder klassiek): warm papierwit `#f6f2e9`, tekst `#2b2823`, koppen donkergroen `#26382b` in **Source Serif 4**, lopende tekst DM Sans 18px, messing accent `#7d6216` (links, regel boven de kop in hoofdletters), groene menubalk/footer `#314336` met lichtgeel `#f0dc8a`, knoppen donkergroen met hoekjes van 2px. Startpagina: tekst links, foto rechts (foto: legging Voorstraat 1, `src/assets/startfoto-voorstraat-1.jpg`; uitsnede in `index.astro` → `FOTO_POSITIE`). Ronde pijlknop op de rand van de foto klapt de foto uit over de hele breedte en verbergt de tekst (Esc of nogmaals klikken = terug); op mobiel wordt de fotoband schermhoog. Hoofdmenu-hover = licht vlak met donkergroene tekst (`--menu-hover-vlak/-tekst`), het omgekeerde van het submenu. Adres- en persoonspagina's: leggingsfoto als band bovenaan (`--fotoband-hoogte`), tekst op de effen pagina. Alternatieve koplettertypes geïnstalleerd: Fraunces, Forum. Vergelijkingsscreenshots in `demo-huisstijl/`. De oude donkere stijl staat in de kopie `stolpersteine-v131211/` en in git.
- **Back-office** (13-11-2026): Decap CMS 3.16.3 op `/admin/` (`src/pages/admin/index.astro`, instellingen `public/admin/config.yml`). Lokaal: `npm run beheer` (decap-server op 8081 + astro dev op 4321), launch-config "beheer". Collecties: **Aanvragen** (`beheer/aanvragen/*.md`, status 1–8, niet gepubliceerd, persoonsgegevens → repo privé houden), **Stenen** (`src/content/stenen/*.json`, één per persoon, bron van de lijst op /gelegd/#lijst; eenmalig gemaakt met `scripts/stenen_omzetten.py` uit `overzicht.json`, dat nu alleen archief is), **Adrespagina's**, **Overige pagina's**. Aanvraag = één adres met een lijst `personen` (naam, geboren, overleden, link, inscriptie, steen). Opmaak back-office: `src/styles/admin.css` (selectors op Decap-namen als `-AppHeader`) + huisstijl.css; voorvertoningen per collectie in `src/pages/admin/index.astro`; de CSS daarvoor wordt van de startpagina opgehaald (geen `?url`-imports: die lekten in dev naar de admin zelf). Menubalk en inhoud max. 1200px breed, gecentreerd. Daar ook een beveiliging: bij een directe sprong tussen bewerkschermen herlaadt de pagina (Decap hield anders velden van het vorige item vast). Online inloggen vereist nog GitHub-repo + OAuth (`backend.repo` in config.yml is TODO). `/admin/` staat in robots.txt als Disallow. Admin-knop in de footer (`site.json` → `admin`).
- **Focuspunt foto's** (13-11-2026): veld `foto_focus: "x y"` (0–1) bij adres- en persoonspagina's = waar de stenen op de foto liggen. `src/lib/foto.ts` geeft `--ratio --fx --fy` mee; `.met-foto::before` in basis.css rekent met `max()`/`clamp()` voor elke schermverhouding de grootte en positie uit zodat dat punt in het midden van de fotoband valt (zonder lege rand; waar de foto precies schermbreed is kan hij horizontaal niet verschuiven). Alle 73 pagina's met foto ingesteld en visueel gecontroleerd op 1440×900, 1024×768, 768×1024, 390×844. Ook invulbaar in de back-office.
- **14-11-2026:** Voor wie heeft een Ken Burns-diavoorstelling (`galerij_weergave: diavoorstelling`, `components/Diavoorstelling.astro`, alleen CSS). Utrecht in de oorlog toont de foto onbijgesneden (`foto_volledig: true`). Paginaveld `foto_credit` voor fotograaf/bron (inventarisatie: `CONTROLE-fotorechten-14112026.md`). Footer (gewijzigd 14-11): "Contact: e-mail" en "Kijken: Stolpersteine - World's Largest Memorial" elk op één regel (`naast: true` in site.json; `.footer__regel`: nowrap, 16px, op smalle telefoons kleiner via `min(1rem, 3.94vw)`) | knoppen Steun ons + Word vrijwilliger naast elkaar; video's weer weggehaald. Recent gelegd: variant B gekozen: bomenfoto vast als achtergrond van de hele pagina met donkergroene laag, witte tekst, stenen met lichtmessing rand (`.pagina--recent-gelegd` in basis.css).
- Schema: lege velden uit de back-office ("" of null) gelden als niet ingevuld (`leeg()` in content.config.ts).
- De omzetscripts weigeren nu te draaien zonder `--forceer` (zouden handwerk overschrijven).

**Werkmap = `website/`.** `stolpersteine-v131211/` is een vastgezette, volledige kopie van 13-11-2026 (commit 1adc01e, met `_omzetscripts/`). Niet in werken en niet wijzigen; alleen als reserve/vergelijking.

Eigen git-repository in `website/` (branch `main`, nog geen remote). Dev-server: `.claude/launch.json` → "website" (poort 4321).

**Huisstijl wijzigen = alleen `website/src/styles/huisstijl.css` openen.** Daar staan alle kleuren, kleurrollen (header, footer, knoppen, hero, kaart, logo), lettertypen (via @fontsource, zelf gehost) en maten als CSS-variabelen. `basis.css` gebruikt uitsluitend die variabelen. Zet nooit kleuren of maten in pagina's of in `basis.css`; voeg zo nodig een variabele toe aan huisstijl.css. Pagina's gebruiken alleen klassen uit basis.css (inhoudsopgave bovenaan dat bestand).

| Wat | Waar |
|---|---|
| Menu, footer, sitenaam, copyright | `src/data/site.json` |
| Header/footer/head-HTML | `src/layouts/Basis.astro` |
| Logo (SVG, kleuren via variabelen) | `src/components/Logo.astro`, favicon `public/favicon.svg` |
| Adrespagina's | `src/content/adressen/<slug>.md` (schema in `src/content.config.ts`), sjabloon `src/pages/[slug].astro` |
| Kaart `/maps/` | `src/pages/maps.astro` (Leaflet + OSM), punten uit adresbestanden + `src/data/kaart-import.json` |
| Homepage | `src/pages/index.astro` |

- Adresbestand: `adres`, `slug` (= oude URL), `gelegd`, optioneel `aantal_stenen` (alleen als de bron het noemt), `titel` (h1; anders is het adres de h1), `personen` [{naam, link?}], `lat`/`lng`, `foto` (achtergrond, in `src/assets/adressen/`; de bron-URL staat als `background-image` in de html-back-up), `uitlijning` (links/rechts op de foto), `notitie`, `bron`.
- Na een wijziging in `content.config.ts` pakt de dev-server die soms niet op: stop de server, verwijder `website/.astro` en start opnieuw.
- Op verzoek van de gebruiker zijn spelfouten hersteld ("bij het Het" en "Shuitevoerder"). Verder blijft de tekst letterlijk. Verhaal als Markdown eronder. Coördinaten opzoeken via PDOK Locatieserver.
- `kaart-import.json`: 101 punten uit de Google My Maps-kaart (laag "tm juni 2024"); 61 zonder coördinaten zijn via PDOK aangevuld (veld `geocode`).
- **Alle 46 adrespagina's zijn omgezet** (13-11-2026) met `scripts/adressen_omzetten.py` (in de back-upmap, niet in de website-repo). Opnieuw draaien overschrijft alles behalve bestanden met `handmatig: true` (Leliestraat 50 bis, Voorstraat 1). Rapport: `scripts/rapport-adressen.txt`. Het script kent per slug correcties: `TEKSTCORRECTIES`, `AFKAPPEN`, `ADRES`, `ZOEK`, `ADRESCORRECTIES`.
- Pagina's met een standaardkop krijgen gegevens + kopregel; afwijkende pagina's (`eigen_opmaak: true`: Nieuwe Koekoekstraat 81, Bilderdijkstraat 15 bis, Boomstraat 13, Domplein 29, Nieuwegracht 92, Julianaweg 22, Amsterdamsestraatweg 313, Obrechtstraat 64) staan in hun geheel letterlijk in de tekst. `personen` is nog leeg bij omgezette pagina's (namen staan in de tekst).
- Kaart: eigen adrespagina's + punten uit de oude Google-kaart; ontdubbeld op naam en op afstand (~25 m).
- **Alle overige pagina's zijn omgezet** (13-11-2026) met `scripts/paginas_omzetten.py` naar `website/src/content/paginas/` (soort: info, persoon, video). Rapport: `scripts/rapport-paginas.txt`. Galerijen en de diavoorstelling (voor wie) staan als `galerij:` in de gegevens; foto's in `src/assets/paginas/`. Bijlagen houden hun oude pad onder `public/wp-content/uploads/`.
- Sjablonen: `src/pages/[slug].astro` kiest `components/AdresPagina.astro` of `components/Pagina.astro`. Menupagina's zonder inhoud (gelegd, nieuws) tonen knoppen naar hun subpagina's uit `site.json`.
- `/locatie-volgens-sheets/` = `src/pages/locatie-volgens-sheets.astro` met `src/data/overzicht.json` (302 rijen uit de Ninja Tables-tabel, met zoekveld). Bevat ook rijen "nog niet geplaatst" (net als live).
- Niet meegenomen (testpagina's): elementor-14576, nieuwe-map, nieuwe-pagina-voor, ninja-table-pro, nog-niet-klaar, recent-gelegd-dupliceren-4830, tablepress-tabel, youtube-test en de twee concepten. Links naar /nog-niet-klaar/ en /vondellaan-24/ (ook live 404) zijn tekst geworden.
- `/stolpersteine-struikelstenen-utrecht/` (oude homepage-URL) verwijst door naar `/` (astro.config.mjs → redirects).
- Contact: het WPForms-formulier is vervangen door het e-mailadres.
- **Zoeken** (13-11-2026): Pagefind. `npm run build` = `astro build && pagefind --site dist`; alleen `<main data-pagefind-body>` wordt geïndexeerd. Zoekpagina `src/pages/zoeken.astro` (ook `/zoeken/?q=…`), vergrootglas in de menubalk (`--zoekknop`). Werkt niet in `npm run dev`: test met launch-config "website-gebouwd" (`npm run preview`, poort 4322) na een build. Uitsluiten van de index: `data-pagefind-ignore`.
- Nog te doen: Pagefind-zoekfunctie, overige pagina's, overzicht (vervanger locatie-volgens-sheets), hosting.

## Open vragen voor de gebruiker

1. **Wie bewerkt straks?** Er zijn meer WordPress-beheerders (Martijn Dekker, Piet, een gedeeld account "stolpesteine utrecht"). Dit jaar zijn er ~30 pagina's bewerkt en er komen geregeld nieuwe adressen bij. Als vrijwilligers zelf moeten kunnen bewerken: een CMS zoals Pages CMS of Decap toevoegen.
2. GitHub-repository: aanmaken en aan de sessie koppelen. Aan het begin van het vorige gesprek was de GitHub-koppeling niet actief.
3. Wat gebeurt er met het oude persoonsmodel? Omzetten naar adrespagina's, of laten zoals het is?
4. Testpagina's, potentiele-adressen en "nog niet klaar": wat gaat mee?
5. Wordt WordPress bevroren tijdens de overstap? Wijzigingen na 13-11-2026 zitten niet in deze back-up.

## Toegang tot de live WordPress (alleen nodig voor nieuwe inhoud)

- Omgevingsvariabelen `WP_URL`, `WP_USER` en `WP_APP_PASSWORD` (applicatiewachtwoord, gebruiker "Claude", rol beheerder).
- **XML-RPC werkt** (`/xmlrpc.php`, bijvoorbeeld `wp.getPosts` met `post_status: any`). De **REST API werkt niet** (`rest_not_logged_in`): de hosting geeft de Authorization-header niet door. Plugins en instellingen zijn daardoor niet te beheren.
- Cloudflare geeft **429** bij te veel verzoeken. Pauzeer ~1,5 s per XML-RPC-call, gebruik maximaal 3 parallelle downloads en probeer opnieuw met backoff.
- Wijzig niets op de live site zonder toestemming. Zet geen wachtwoorden in de chat of in bestanden.
