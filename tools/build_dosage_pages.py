"""Build one page per dosage form (tablets.html, capsules.html, syrups.html, ointments.html)
from the product cards in products.html, which stays the single source of truth.

Each page lists only that form's products as static HTML (good for SEO), with search and
therapeutic-area chips for the areas present. Re-run after editing products.html:

    py tools/build_dosage_pages.py
    py tools/seo_head.py
"""
import os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = open(os.path.join(root, "products.html"), encoding="utf-8").read()

# form key -> page settings
FORMS = {
    "tablets": {
        "title": "Tablets", "icon": "i-tablet", "tone": "green",
        "lead": "Oral solid dosage tablets across all major therapies: pain, infection, diabetes, hypertension, allergy and gastro-intestinal care.",
    },
    "capsules": {
        "title": "Capsules", "icon": "i-capsule", "tone": "teal",
        "lead": "Oral solid dosage (OSD) capsule formulations, made to order to the buyer's requirement.",
    },
    "syrups": {
        "title": "Syrups", "icon": "i-syrup", "tone": "orange",
        "lead": "Syrups, suspensions and dry syrups, including paediatric strengths, in 60ml and 100ml packs.",
    },
    "ointments": {
        "title": "Ointments", "icon": "i-tube", "tone": "blue",
        "lead": "Topical ointment formulations, manufactured according to the need of the buyer or the demand in the market.",
    },
}

AREAS = [
    ("anti-infective", "Anti-infective"), ("analgesic", "Analgesic"), ("anti-diabetic", "Anti-diabetic"),
    ("antibiotic", "Antibiotic"), ("anti-hypertensive", "Anti-hypertensive"),
    ("anti-allergic", "Anti-allergic"), ("gastro-intestinal", "Gastro-intestinal"),
]

cards = re.findall(r'(<article class="product-card".*?</article>)', src, re.S)
if not cards:
    sys.exit("No product cards found in products.html")


def form_of(card):
    return re.search(r'data-form="([^"]+)"', card).group(1)


def areas_of(card):
    return re.search(r'data-area="([^"]+)"', card).group(1).split()


def switcher(current):
    links = ['<a class="form-switch__link" href="products.html"><svg class="icon icon--sm"><use href="#i-layers"/></svg>All products</a>']
    for key, f in FORMS.items():
        attr = ' aria-current="page"' if key == current else ""
        links.append(f'<a class="form-switch__link form-switch__link--{f["tone"]}" href="{key}.html"{attr}>'
                     f'<svg class="icon icon--sm"><use href="#{f["icon"]}"/></svg>{f["title"]}</a>')
    return ('        <nav class="form-switch" aria-label="Dosage forms">\n          '
            + "\n          ".join(links) + "\n        </nav>\n")


def catalogue(key, f, items):
    noun = f["title"].lower()
    if not items:
        return f"""        <div class="enquiry-panel" data-reveal>
          <span class="form-card__icon form-card--{f['tone']}"><svg class="icon"><use href="#{f['icon']}"/></svg></span>
          <div>
            <h2 id="catalogue-title">{f['title']} available on enquiry</h2>
            <p>We don't list {noun} as catalogue brands. Tell us the molecule, strength and quantity you need and we'll manufacture it through our partner plants.</p>
          </div>
          <div class="enquiry-panel__actions">
            <a class="btn btn--primary" href="contact.html?interest=finished-dosages&amp;product={f['title']}#enquiry">Enquire about {noun} <svg class="icon icon--sm icon--arrow"><use href="#i-arrow-right"/></svg></a>
            <a class="btn btn--ghost" href="products.html">See all products</a>
          </div>
        </div>
"""
    present = {a for c in items for a in areas_of(c)}
    chips = "\n".join(
        f'            <button class="chip" type="button" data-filter="{k}" aria-pressed="false">{label}</button>'
        for k, label in AREAS if k in present)
    body = "\n          ".join(c.strip() for c in items)
    return f"""        <div class="section-head section-head--split" data-reveal>
          <div>
            <p class="eyebrow">Our brands</p>
            <h2 id="catalogue-title">{f['title']} catalogue</h2>
          </div>
          <p class="result-count" data-filter-count aria-live="polite"></p>
        </div>

        <div class="catalogue-panel" data-reveal>
          <label class="search">
            <span class="sr-only">Search {noun}</span>
            <svg class="icon"><use href="#i-search"/></svg>
            <input type="search" placeholder="Search brand or molecule…" data-filter-search autocomplete="off">
          </label>
          <div class="catalogue-panel__areas">
          <span class="catalogue-panel__label">Therapeutic area</span>
          <div class="chip-group" data-filter-group="area" role="group" aria-label="Filter by therapeutic area">
            <button class="chip" type="button" data-filter="all" aria-pressed="true"><svg class="icon"><use href="#i-filter"/></svg>All areas</button>
{chips}
          </div>
          </div>
        </div>

        <div class="grid grid--cards product-grid" style="--min:260px" data-stagger>
          {body}
        </div>

        <div class="empty-state" data-filter-empty hidden>
          <p><strong>No {noun} match this filter.</strong></p>
          <p>More formulations are available on request.</p>
          <p style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:0">
            <button class="btn btn--ghost btn--sm" type="button" data-filter-reset>Clear filters</button>
            <a class="btn btn--primary btn--sm" href="contact.html?interest=finished-dosages#enquiry">Ask about a product</a>
          </p>
        </div>
"""


def page(key, f):
    items = [c for c in cards if form_of(c) == key]
    n = len(items)
    n_areas = len({a for c in items for a in areas_of(c)})
    facts = (f"""          <ul class="banner-facts" role="list" data-reveal data-reveal-delay="280">
            <li><strong>{n}</strong><span>Listed brand{'s' if n != 1 else ''}</span></li>
            <li><strong>{n_areas}</strong><span>Therapeutic area{'s' if n_areas != 1 else ''}</span></li>
            <li><strong>WHO-GMP</strong><span>Partner plants</span></li>
          </ul>
""" if n else """          <ul class="banner-facts" role="list" data-reveal data-reveal-delay="280">
            <li><strong>Custom</strong><span>Made to your need</span></li>
            <li><strong>WHO-GMP</strong><span>Partner plants</span></li>
          </ul>
""")
    browse = (f'<a class="btn btn--primary" href="#catalogue">Browse {f["title"].lower()} <svg class="icon icon--sm icon--arrow"><use href="#i-arrow-right"/></svg></a>'
              if n else
              f'<a class="btn btn--primary" href="contact.html?interest=finished-dosages&amp;product={f["title"]}#enquiry">Enquire now <svg class="icon icon--sm icon--arrow"><use href="#i-arrow-right"/></svg></a>')
    return f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<!-- seo:start -->
<!-- seo:end -->
</head>
<!-- Generated by tools/build_dosage_pages.py from products.html. Edit products.html, then re-run the tool. -->
<body data-cta-title="Looking for a specific formulation?" data-cta-text="We can manufacture according to the need of the buyer or the demand in the market." data-cta-href="contact.html?enquiry=catalogue#enquiry" data-cta-label="Request catalogue">
  <div data-include="header"></div>

  <main id="main">
    <section class="page-banner page-banner--{f['tone']}" aria-labelledby="page-title">
      <div class="container container--wide page-banner__inner">
        <div class="page-banner__text">
          <nav aria-label="Breadcrumb"><ol class="breadcrumb"><li><a href="index.html"><svg class="icon icon--sm"><use href="#i-home"/></svg>Home</a></li><li><a href="products.html">Finished Dosages</a></li><li><span aria-current="page">{f['title']}</span></li></ol></nav>
          <p class="eyebrow" data-reveal>Finished dosages</p>
          <h1 id="page-title" data-reveal data-reveal-delay="80">{f['title']}</h1>
          <p class="lead" data-reveal data-reveal-delay="160">{f['lead']}</p>
          <div class="banner-actions" data-reveal data-reveal-delay="220">
            {browse}
            <a class="btn btn--ghost" href="products.html">All products</a>
          </div>
{facts}        </div>
        <div class="banner-art banner-art--form form-card--{f['tone']}" aria-hidden="true"><div class="banner-art__ring"></div><div class="banner-art__core glass"><svg class="icon"><use href="#{f['icon']}"/></svg></div></div>
      </div>
    </section>

    <section class="section section--tint" id="catalogue" aria-labelledby="catalogue-title">
      <div class="container container--wide" data-filter-scope data-filter-noun="{f['title'].lower()}">
{switcher(key)}
{catalogue(key, f, items)}      </div>
    </section>
  </main>

  <div data-include="footer"></div>

  <script src="assets/js/main.js" defer></script>
  <script src="assets/js/menu.js" defer></script>
  <script src="assets/js/animations.js" defer></script>
</body>
</html>
"""


for key, f in FORMS.items():
    out = os.path.join(root, key + ".html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page(key, f))
    print("built", key + ".html", "-", sum(form_of(c) == key for c in cards), "products")
