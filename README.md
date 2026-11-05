# Plaksha Industries — Website

Static, multi-page website for **Plaksha Industries Pvt. Ltd.** ("Working towards Healthier Life").
Plain HTML, CSS and vanilla JavaScript: no framework, no build step. All content comes from the
company profile PPT (see [content.md](content.md)).

## Run it locally

The header and footer are loaded with `fetch()`, so the site must be served over http.
Opening an `.html` file directly (`file://`) will show pages without a header/footer.

```bash
py -m http.server 5500
```

Then open http://localhost:5500. Any static server works (VS Code Live Server, `npx serve`, Apache, Nginx).

## Folder structure

```
index.html  about.html  products.html  tablets.html  capsules.html  syrups.html  ointments.html
api-intermediates.html  manufacturing.html
quality.html  research.html  why-us.html  contact.html  404.html
.htaccess                  Apache: serves 404.html for missing URLs
components/
  header.html              logo, nav, dropdowns, mega menu, mobile drawer, icon sprite (#i-*)
  footer.html              enquiry CTA card, brand, links, visit card (map + contact), copyright
assets/
  css/
    variables.css          design tokens: colours (light + dark), type scale, 8px spacing, radius, shadows
    base.css               reset, typography, layout, utilities
    components.css         buttons, cards, header/nav/mega menu, footer, tabs, accordion, timeline,
                           steps, CTA band, forms, tables, filters + all motion (reveal, preloader…)
    pages.css              hero, page banners, page-specific sections
  js/
    theme.js               dark/light (localStorage → OS preference); runs in <head> before paint
    main.js                header/footer include, tabs, accordion, filters/search, #hash routing, form
    menu.js                sticky header, dropdown + mega menu (hover/click/keyboard), mobile drawer
    animations.js          scroll reveals, counters, progress bar, parallax, back-to-top,
                           page fade, ripple, magnetic CTAs, section highlight
  img/
    brand/                 logo, tree mark, favicon (transparent PNG)
    photos/                hero photo (JPG + WebP, 640px and 1150px)
    products/              slide-7 brand list (reference)
    illustrations/         molecule pattern (SVG)
    og/                    1200×630 social share image
content.md                 all text from the PPT, palette, open questions for the client
tools/seo_head.py          regenerates the <head> (meta, OG, schema.org) of every page
tools/build_dosage_pages.py  builds tablets/capsules/syrups/ointments.html from products.html
tests/site_check.py        Playwright test suite (see below)
```

## Customising

**Colours and fonts.** Everything comes from CSS variables in `assets/css/variables.css`. The light theme
is in `:root`, the dark theme in `:root[data-theme="dark"]`. The site uses **flat colours only**: no
gradients anywhere (`tests/site_check.py` fails if the word "gradient" appears in any css/html/js/svg file).

**Header, menu, footer.** Edit `components/header.html` / `components/footer.html` once; every page picks
them up. The active menu item comes from each `<li data-page="…">` (file names without `.html`).

**Icons.** Inline SVG sprite at the top of `components/header.html`. Use one with
`<svg class="icon"><use href="#i-flask"/></svg>`. To add an icon, add a `<symbol id="i-name">`.

**Page title, description, social tags.** Edit the `PAGES` list in `tools/seo_head.py`, then run
`py tools/seo_head.py`. It rewrites only the block between `<!-- seo:start -->` and `<!-- seo:end -->`.
The site URL is set at the top (`SITE`); it currently assumes `https://www.plakshaindustries.com/`.

**Products.** Product cards are plain HTML in `products.html`. Filtering reads `data-area` and `data-form`
on each `[data-filter-item]`; the search covers the card text. APIs/intermediates are table rows in
`api-intermediates.html` (`data-cat` drives the API category chips).

`tablets.html`, `capsules.html`, `syrups.html` and `ointments.html` are generated from the cards in
`products.html`, so never edit them by hand. After adding, removing or changing a product in
`products.html`, run `py tools/build_dosage_pages.py` then `py tools/seo_head.py`. Also update the
hand-typed counts on `products.html` (banner numbers and the brand count on each dosage-form card).

**Enquiry form.** By default the form validates, then opens the visitor's email app addressed to
`data-mailto`. To send without the email app, create a Formspree form and set
`data-endpoint="https://formspree.io/f/XXXXXXX"` on the `<form>` in `contact.html`.

**Animations.** Add `data-reveal` to any element (`left`, `right`, `zoom`, `clip` variants;
`data-reveal-delay="200"`), `data-stagger` to a parent to stagger its children, and
`data-count="25" data-suffix="+"` for counters. All motion is switched off for visitors who set
"reduce motion" in their OS. The logo preloader shows once per browser session and is gone within 1 second.

**Footer call-to-action.** The footer opens with an enquiry card (title, text, button, phone).
The default text is in `components/footer.html`; a page can show its own message with
`<body data-cta-title="…" data-cta-text="…" data-cta-href="contact.html#enquiry" data-cta-label="Send Enquiry">`,
or hide the card with `<body data-cta="off">` (used on the contact page).

**Map.** The Google Maps embed lives in the footer's visit card (`components/footer.html`) and on
`contact.html`. Pages with their own map add `class="has-map-section"` on `<body>` to hide the footer copy.

## Testing

```bash
py -m pip install playwright
py tests/site_check.py
```

Uses the installed Microsoft Edge (no browser download). It starts its own server on port 5599 and checks:

- every page in light + dark at 1440 / 768 / 360 px: console errors, failed requests, horizontal
  overflow, broken images, header/footer present, one `<h1>`
- internal links and asset paths, and the "no gradient" rule
- mega menu, dropdown keyboard, mobile drawer, theme toggle, filters, tabs, accordion, enquiry
  form (with a stubbed Formspree endpoint, nothing is sent), counters, back-to-top, preloader,
  page transition

Full-page screenshots (light/dark × desktop/mobile) are written to `tests/screenshots/`.
They are regenerated on every run and don't need to be deployed.

## Deploying

Upload everything except `tests/`, `tools/`, `content.md`, the `.pptx` and `Plaksha_Logo.png`.
CSS and JS are written readable and are safe to minify with any standard minifier if needed.
`404.html` uses `<base href="/">`, so it assumes the site sits at the domain root.

## Open items for the client

See the end of [content.md](content.md): working hours, final domain, Formspree ID, product catalogue
PDF, real facility/founder photos, and a review of the therapy tags used for filtering.
