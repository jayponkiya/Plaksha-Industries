"""Plaksha site check (Playwright + the installed Microsoft Edge).

Runs a local server, then for every page:
  - light + dark  x  desktop 1440 / tablet 768 / mobile 360
  - console errors, page errors, failed same-origin requests
  - horizontal overflow, broken images, broken internal links
  - full-page screenshots (light/dark x desktop/mobile) in tests/screenshots/
plus interaction tests (mega menu, dropdown keyboard, mobile drawer, theme toggle,
filters, tabs, accordion, enquiry form, back-to-top, preloader, page transition)
and a "no gradient" scan of the source files.

usage:  py tests/site_check.py            (pip install playwright first)
"""
import http.server
import json
import os
import re
import socketserver
import sys
sys.stdout.reconfigure(encoding="utf-8")
import threading
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "tests" / "screenshots"
PORT = 5599
BASE = f"http://localhost:{PORT}/"
PAGES = ["index", "about", "products", "api-intermediates", "manufacturing",
         "quality", "research", "why-us", "contact", "404"]
VIEWPORTS = {"desktop": (1440, 900), "tablet": (768, 1024), "mobile": (360, 780)}
EXTERNAL_OK = ("fonts.googleapis.com", "fonts.gstatic.com", "google.com/maps", "maps.gstatic", "googleapis")

problems = []


def problem(where, msg):
    problems.append(f"[{where}] {msg}")
    print(f"  FAIL {where}: {msg}")


def ok(where, msg):
    print(f"  ok   {where}: {msg}")


# ---------------------------------------------------------------- server
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    handler = partial(QuietHandler, directory=str(ROOT))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# ---------------------------------------------------------------- static checks
def check_no_gradient():
    hits = []
    for p in ROOT.rglob("*"):
        if p.suffix.lower() in (".css", ".html", ".js", ".svg") and "tests" not in p.parts:
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if "gradient" in line.lower():
                    hits.append(f"{p.relative_to(ROOT)}:{i}")
    if hits:
        problem("no-gradient", f"{len(hits)} matches: {hits[:5]}")
    else:
        ok("no-gradient", "0 matches in css/html/js/svg")


def check_links():
    files = {p.name for p in ROOT.glob("*.html")}
    missing = set()
    for p in list(ROOT.glob("*.html")) + list((ROOT / "components").glob("*.html")):
        html = p.read_text(encoding="utf-8")
        for href in re.findall(r'(?:href|src|srcset)="([^"#?:]+?\.(?:html|png|jpg|webp|svg|css|js))', html):
            for part in href.split(","):
                f = part.strip().split(" ")[0]
                if f and not (ROOT / f).exists():
                    missing.add(f"{p.name} -> {f}")
    if missing:
        problem("links", f"missing targets: {sorted(missing)}")
    else:
        ok("links", "all internal href/src targets exist")


# ---------------------------------------------------------------- per-page checks
SCROLL_THROUGH = """async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 300));
}"""

PAGE_STATE = """() => {
  const w = document.documentElement.clientWidth;
  const broken = [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.loading !== 'lazy').map(i => i.currentSrc || i.src);
  const brokenLazy = [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.loading === 'lazy').map(i => i.currentSrc || i.src);
  return { overflow: document.documentElement.scrollWidth - w, broken, brokenLazy,
           header: !!document.getElementById('site-header'), footer: !!document.querySelector('.site-footer'),
           h1: document.querySelectorAll('h1').length };
}"""


def page_pass(browser, theme, vp_name, shoot):
    w, h = VIEWPORTS[vp_name]
    ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme, reduced_motion="reduce")
    for name in PAGES:
        where = f"{name} {theme} {vp_name}"
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: errors.append(f"request failed {r.url}")
                if not any(x in r.url for x in EXTERNAL_OK) else None)
        page.on("response", lambda r: errors.append(f"HTTP {r.status} {r.url}")
                if r.status >= 400 and r.url.startswith(BASE) else None)
        page.goto(BASE + name + ".html", wait_until="load")
        page.wait_for_function("window.__plakshaComponentsReady === true", timeout=5000)
        page.evaluate(SCROLL_THROUGH)
        st = page.evaluate(PAGE_STATE)
        if st["overflow"] > 0:
            problem(where, f"horizontal overflow {st['overflow']}px")
        if st["broken"] or st["brokenLazy"]:
            problem(where, f"broken images {st['broken'] + st['brokenLazy']}")
        if not (st["header"] and st["footer"]):
            problem(where, "header/footer include missing")
        if st["h1"] != 1:
            problem(where, f"{st['h1']} <h1> elements")
        real = [e for e in errors if not any(x in e for x in EXTERNAL_OK)]
        if real:
            problem(where, f"console: {real[:3]}")
        if shoot:
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"{name}-{theme}-{vp_name}.png"), full_page=True)
        page.close()
    ctx.close()
    ok(f"pages {theme} {vp_name}", f"{len(PAGES)} pages checked" + (" + screenshots" if shoot else ""))


# ---------------------------------------------------------------- interactions
def interactions(browser):
    # ---- desktop, normal motion
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    # preloader: shown on first view, gone within ~1s
    page.goto(BASE + "index.html", wait_until="domcontentloaded")
    pre = page.evaluate("document.documentElement.classList.contains('is-preloading')")
    page.wait_for_timeout(1100)
    pre_after = page.evaluate("document.documentElement.classList.contains('is-preloading')")
    (ok if pre and not pre_after else problem)("preloader", f"shown={pre}, still shown after 1.1s={pre_after}")
    page.wait_for_function("window.__plakshaComponentsReady === true")

    # mega menu on hover, Esc closes
    page.hover("[aria-controls=dd-products]")
    page.wait_for_timeout(350)
    mega_open = page.get_attribute("[aria-controls=dd-products]", "aria-expanded") == "true"
    page.keyboard.press("Escape")
    mega_closed = page.get_attribute("[aria-controls=dd-products]", "aria-expanded") == "false"
    (ok if mega_open and mega_closed else problem)("mega menu", f"hover opens={mega_open}, Esc closes={mega_closed}")

    # dropdown keyboard: focus About, ArrowDown  ->  first link focused
    page.mouse.move(700, 600)
    page.focus("[aria-controls=dd-about]")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(100)
    focused = page.evaluate("document.activeElement.getAttribute('href')")
    page.keyboard.press("Escape")
    (ok if focused == "about.html#profile" else problem)("dropdown keyboard", f"ArrowDown focused {focused}")

    # theme toggle persists
    page.click("[data-theme-toggle]")
    t1 = page.evaluate("[document.documentElement.dataset.theme, localStorage.getItem('plaksha-theme')]")
    page.reload()
    t2 = page.evaluate("document.documentElement.dataset.theme")
    page.click("[data-theme-toggle]")
    (ok if t1 == ["dark", "dark"] and t2 == "dark" else problem)("theme toggle", f"after click {t1}, after reload {t2}")

    # scroll progress + back-to-top
    page.evaluate("window.scrollTo(0, 2000)")
    page.wait_for_timeout(400)
    prog = page.evaluate("getComputedStyle(document.querySelector('.scroll-progress')).getPropertyValue('--progress')")
    totop = page.evaluate("document.querySelector('.to-top').classList.contains('is-visible')")
    page.click(".to-top")
    page.wait_for_timeout(1200)
    y = page.evaluate("scrollY")
    (ok if float(prog or 0) > 0 and totop and y < 5 else problem)("progress/back-to-top", f"progress={prog}, button={totop}, scrollY after={y}")

    # counters finish on their final value
    page.evaluate("document.querySelector('.trust-strip').scrollIntoView()")
    page.wait_for_timeout(1800)
    vals = page.evaluate("[...document.querySelectorAll('.trust-strip [data-count]')].map(e => e.textContent)")
    (ok if vals == ["25+", "06", "Est. 2020"] else problem)("counters", str(vals))

    # page transition: clicking an internal link fades and navigates
    page.evaluate("window.scrollTo(0,0)")
    page.click(".hero__actions .btn--primary")
    page.wait_for_url("**/products.html")
    ok("page transition", "internal link navigated after fade")

    # products filter + search
    page.wait_for_function("window.__plakshaComponentsReady === true")
    page.click("[data-filter-group=area] [data-filter=analgesic]")
    n = page.evaluate("[...document.querySelectorAll('[data-filter-item]')].filter(e => !e.hidden).length")
    page.fill("[data-filter-search]", "650")
    m = page.evaluate("[...document.querySelectorAll('[data-filter-item]')].filter(e => !e.hidden).length")
    (ok if n == 5 and m == 1 else problem)("product filter", f"analgesic={n}, +search '650'={m}")

    # API tabs via hash + arrow keys
    page.goto(BASE + "api-intermediates.html#intermediates")
    page.wait_for_function("window.__plakshaComponentsReady === true")
    sel = page.evaluate("document.querySelector('[role=tab][aria-selected=true]').id")
    page.focus("#tab-intermediates")
    page.keyboard.press("ArrowRight")
    sel2 = page.evaluate("document.querySelector('[role=tab][aria-selected=true]').id")
    (ok if sel == "tab-intermediates" and sel2 == "tab-specialty" else problem)("tabs", f"hash -> {sel}, ArrowRight -> {sel2}")

    # accordion
    page.goto(BASE + "why-us.html")
    page.click("#faq-2-btn")
    acc = page.get_attribute("#faq-2-btn", "aria-expanded")
    (ok if acc == "true" else problem)("accordion", f"aria-expanded={acc}")

    # enquiry form: validation, then a stubbed Formspree endpoint
    page.goto(BASE + "contact.html?interest=apis&product=Apixaban#enquiry")
    page.wait_for_function("window.__plakshaComponentsReady === true")
    prefill = page.input_value("#f-message")
    page.fill("#f-message", "")
    page.select_option("#f-interest", "")
    page.click("form [type=submit]")
    errs = page.evaluate("[...document.querySelectorAll('.field__error')].filter(e => e.textContent).length")
    page.route("https://formspree.io/**", lambda r: r.fulfill(status=200, body="{}", content_type="application/json"))
    page.evaluate("document.querySelector('form').setAttribute('data-endpoint', 'https://formspree.io/f/test')")
    page.fill("#f-name", "Test User")
    page.fill("#f-email", "test@example.com")
    page.fill("#f-phone", "+91 98795 72661")
    page.select_option("#f-interest", "apis")
    page.fill("#f-message", "Need a quote for Apixaban")
    page.click("form [type=submit]")
    page.wait_for_selector(".form__status.is-success", timeout=3000)
    (ok if "Apixaban" in prefill and errs == 4 else problem)("enquiry form", f"prefill ok={'Apixaban' in prefill}, empty-submit errors={errs}, stubbed send ok")

    if errors:
        problem("desktop interactions", f"page errors {errors[:3]}")
    ctx.close()

    # ---- mobile drawer + accordion
    ctx = browser.new_context(viewport={"width": 360, "height": 780}, color_scheme="dark", has_touch=True, is_mobile=True)
    page = ctx.new_page()
    page.goto(BASE + "index.html")
    page.wait_for_function("window.__plakshaComponentsReady === true")
    page.click("[data-nav-open]")
    page.wait_for_timeout(500)
    opened = page.evaluate("document.getElementById('primary-nav').classList.contains('is-open')")
    page.click("[aria-controls=dd-products]")
    acc = page.get_attribute("[aria-controls=dd-products]", "aria-expanded")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    closed = not page.evaluate("document.getElementById('primary-nav').classList.contains('is-open')")
    (ok if opened and acc == "true" and closed else problem)("mobile drawer", f"open={opened}, accordion={acc}, Esc closes={closed}")
    ctx.close()


# ---------------------------------------------------------------- motion on
HIDDEN_BY_REVEAL = """() => [...document.querySelectorAll('*')].filter(e => {
  const cs = getComputedStyle(e);
  return /inset\\(100%/.test(cs.clipPath) || (e.hasAttribute('data-reveal') && cs.opacity === '0');
}).map(e => e.className || e.tagName)"""


def motion_pass(browser):
    """The page passes run with reduced motion; this one runs with animations ON and makes
    sure every scroll reveal (incl. clip-path image reveals) actually plays."""
    for vp_name in ("desktop", "mobile"):
        w, h = VIEWPORTS[vp_name]
        ctx = browser.new_context(viewport={"width": w, "height": h})
        stuck = {}
        for name in PAGES:
            page = ctx.new_page()
            page.goto(BASE + name + ".html", wait_until="load")
            page.wait_for_function("window.__plakshaComponentsReady === true", timeout=5000)
            page.evaluate("""async () => { for (let y = 0; y < document.body.scrollHeight; y += 300) {
              scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); } }""")
            page.wait_for_timeout(1500)
            left = page.evaluate(HIDDEN_BY_REVEAL)
            if left:
                stuck[name] = left[:4]
            page.close()
        ctx.close()
        if stuck:
            problem(f"reveals {vp_name}", f"still hidden after scrolling: {stuck}")
        else:
            ok(f"reveals {vp_name}", "every reveal played with animations on")


# ---------------------------------------------------------------- main
def main():
    check_no_gradient()
    check_links()
    httpd = serve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge")
        for theme in ("light", "dark"):
            for vp in VIEWPORTS:
                page_pass(browser, theme, vp, shoot=vp != "tablet")
        motion_pass(browser)
        interactions(browser)
        browser.close()
    httpd.shutdown()
    print("\n" + ("ALL CHECKS PASSED" if not problems else f"{len(problems)} PROBLEM(S):\n" + "\n".join(problems)))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
