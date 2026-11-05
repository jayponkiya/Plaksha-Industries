"""Fill the <!-- seo:start --> … <!-- seo:end --> block of every page with the shared <head>:
meta, canonical, Open Graph / Twitter tags, fonts, CSS and schema.org JSON-LD. Idempotent."""
import json, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = "https://www.plakshaindustries.com/"  # assumed from the email domain — confirm
OG_IMAGE = SITE + "assets/img/og/plaksha-og.jpg"

PAGES = {
    "index.html": ("Plaksha Industries Pvt. Ltd. | Working towards Healthier Life",
                   "Plaksha Industries Pvt. Ltd., Ahmedabad: Finished Dosages (Tablets, Capsules, Syrups, Ointments), APIs, Key Starting Materials, Intermediates and Specialty Chemicals."),
    "about.html": ("About Us | Plaksha Industries Pvt. Ltd.",
                   "Established in 2020, Plaksha Industries is a healthcare venture with a vision to become a global healthcare organization through quality and affordable products."),
    "products.html": ("Finished Dosages: Tablets, Capsules, Syrups | Plaksha Industries",
                      "Generic finished dosage portfolio across anti-infective, analgesic, anti-diabetic, antibiotic, anti-hypertensive, anti-allergic and gastro-intestinal therapies."),
    "api-intermediates.html": ("APIs, Intermediates & Specialty Chemicals | Plaksha Industries",
                               "Active Pharmaceutical Ingredients (Acyclovir, Vildagliptin, Febuxostat, Montelukast, Pregabalin, Apixaban and more), Key Starting Materials, Intermediates and Specialty Chemicals."),
    "manufacturing.html": ("Manufacturing Facility & Services | Plaksha Industries",
                           "Technical collaboration with 06 pharmaceutical manufacturing plants in India for OSD, Syrup and Ointment, with bulk, urgent and custom manufacturing."),
    "quality.html": ("Quality & WHO-GMP | Plaksha Industries Pvt. Ltd.",
                     "Products manufactured under strict WHO GMP compliances, meeting national and international quality standards for safe medical supplies."),
    "research.html": ("R&D Lab | Plaksha Industries Pvt. Ltd.",
                      "A full R&D Lab set-up and a team of 25+ scientists with 2–25 years of experience, working in the lab and in the plant."),
    "why-us.html": ("Why Choose Us | Plaksha Industries Pvt. Ltd.",
                    "Nine reasons to partner with Plaksha: WHO GMP manufacturing, 25+ scientists, full R&D lab, a wide portfolio and manufacturing to your need."),
    "contact.html": ("Contact Us | Plaksha Industries Pvt. Ltd.",
                     "Contact Plaksha Industries, 103 Shivam Industrial Park, Changodar, Ahmedabad, Gujarat 382213. Email yogendra@plakshaindustries.com or call +91 98795 72661."),
    "404.html": ("Page not found | Plaksha Industries Pvt. Ltd.",
                 "The page you are looking for could not be found."),
}

ORG = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Plaksha Industries Pvt. Ltd.",
    "alternateName": "Plaksha",
    "slogan": "Working towards Healthier Life",
    "url": SITE,
    "logo": SITE + "assets/img/brand/plaksha-logo-full.png",
    "image": OG_IMAGE,
    "foundingDate": "2020",
    "email": "yogendra@plakshaindustries.com",
    "telephone": "+91-9879572661",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "103, Shivam Industrial Park, Nr Parikh Packaging, Changodar",
        "addressLocality": "Ahmedabad",
        "addressRegion": "Gujarat",
        "postalCode": "382213",
        "addressCountry": "IN",
    },
    "founder": [
        {"@type": "Person", "name": "Aradhana Chauhan", "jobTitle": "Founder Director"},
        {"@type": "Person", "name": "Yogendra Chauhan", "jobTitle": "Founder Director"},
    ],
    "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "sales",
        "telephone": "+91-9879572661",
        "email": "yogendra@plakshaindustries.com",
        "areaServed": "Worldwide",
    },
}


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def head(file, title, desc):
    url = SITE + ("" if file == "index.html" else file)
    robots = '\n  <meta name="robots" content="noindex">' if file == "404.html" else ""
    base = '\n  <base href="/">' if file == "404.html" else ""
    canonical = "" if file == "404.html" else f'\n  <link rel="canonical" href="{url}">'
    return f"""<!-- seo:start -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{base}
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">{canonical}{robots}
  <meta name="theme-color" content="#1b7413">
  <link rel="icon" type="image/png" href="assets/img/brand/favicon-192.png">
  <link rel="apple-touch-icon" href="assets/img/brand/favicon-192.png">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Plaksha Industries Pvt. Ltd.">
  <meta property="og:locale" content="en_IN">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Plaksha Industries: Working towards Healthier Life">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(desc)}">
  <meta name="twitter:image" content="{OG_IMAGE}">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap" rel="stylesheet">

  <script src="assets/js/theme.js"></script>
  <link rel="stylesheet" href="assets/css/variables.css">
  <link rel="stylesheet" href="assets/css/base.css">
  <link rel="stylesheet" href="assets/css/components.css">
  <link rel="stylesheet" href="assets/css/pages.css">

  <script type="application/ld+json">
{json.dumps(ORG, indent=2, ensure_ascii=False)}
  </script>
<!-- seo:end -->"""


pat = re.compile(r"<!-- seo:start -->.*?<!-- seo:end -->", re.S)
for file, (title, desc) in PAGES.items():
    path = os.path.join(root, file)
    if not os.path.exists(path):
        print("skip (missing)", file)
        continue
    html = open(path, encoding="utf-8").read()
    if not pat.search(html):
        print("skip (no marker)", file)
        continue
    html = pat.sub(lambda m: head(file, title, desc), html, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("seo ok", file)
