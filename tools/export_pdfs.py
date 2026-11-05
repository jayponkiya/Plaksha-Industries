"""Export the site as two PDFs, light and dark, desktop view (1440px wide).
Each site page becomes one PDF page: a title bar with the page name, then the full-page screenshot.

usage:  py tools/export_pdfs.py          (needs playwright + Pillow; uses installed Microsoft Edge)
output: exports/Plaksha-Website-Light-Desktop.pdf, exports/Plaksha-Website-Dark-Desktop.pdf
"""
import http.server
import socketserver
import threading
from functools import partial
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "exports"
PORT = 5598
BASE = f"http://localhost:{PORT}/"
WIDTH, HEIGHT = 1440, 900

PAGES = [
    ("index", "Home"),
    ("about", "About Us"),
    ("products", "Products: Finished Dosages"),
    ("tablets", "Products: Tablets"),
    ("capsules", "Products: Capsules"),
    ("syrups", "Products: Syrups"),
    ("ointments", "Products: Ointments"),
    ("api-intermediates", "APIs & Intermediates"),
    ("manufacturing", "Manufacturing"),
    ("quality", "Quality"),
    ("research", "R&D Lab"),
    ("why-us", "Why Us"),
    ("contact", "Contact"),
]

THEMES = {
    "light": {"bar": (237, 245, 240), "title": (11, 26, 18), "sub": (74, 94, 83), "line": (27, 116, 19)},
    "dark": {"bar": (15, 31, 25), "title": (244, 250, 246), "sub": (167, 187, 176), "line": (76, 201, 60)},
}

SCROLL_THROUGH = """async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 400));
}"""


# Map iframes are loading="lazy": load them eagerly and wait (max 10s) so the screenshot shows the map
LOAD_MAPS = """async () => {
  const frames = [...document.querySelectorAll('iframe')];
  await Promise.all(frames.map(f => new Promise(done => {
    f.addEventListener('load', done, { once: true });
    setTimeout(done, 10000);
    f.loading = 'eager';
    f.src = f.src;
  })));
}"""


def font(size, bold=False):
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def with_title(shot, title, file, theme):
    c = THEMES[theme]
    bar_h = 120
    img = Image.new("RGB", (shot.width, shot.height + bar_h), c["bar"])
    d = ImageDraw.Draw(img)
    d.text((48, 26), title, font=font(40, bold=True), fill=c["title"])
    d.text((48, 78), f"{file}.html  ·  {theme} mode  ·  desktop {WIDTH}px", font=font(20), fill=c["sub"])
    d.rectangle([0, bar_h - 6, shot.width, bar_h], fill=c["line"])
    img.paste(shot.convert("RGB"), (0, bar_h))
    return img


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    OUT.mkdir(exist_ok=True)
    tmp = OUT / "_shots"
    tmp.mkdir(exist_ok=True)
    httpd = socketserver.TCPServer(("", PORT), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge")
            for theme in THEMES:
                ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT},
                                          color_scheme=theme, reduced_motion="reduce")
                pages = []
                for file, title in PAGES:
                    page = ctx.new_page()
                    page.goto(BASE + file + ".html", wait_until="load")
                    page.wait_for_function("window.__plakshaComponentsReady === true", timeout=8000)
                    page.evaluate(LOAD_MAPS)
                    page.evaluate(SCROLL_THROUGH)
                    # A full-page screenshot leaves cross-origin map iframes blank, so shoot each
                    # map on screen and paste it back in at its document position
                    maps = []
                    frames = page.locator("iframe")
                    for i in range(frames.count()):
                        f = frames.nth(i)
                        if not f.is_visible():
                            continue
                        f.scroll_into_view_if_needed()
                        page.wait_for_timeout(2500)
                        pos = f.evaluate("e => { const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY]; }")
                        part = tmp / f"{file}-{theme}-map{i}.png"
                        f.screenshot(path=str(part))
                        maps.append((part, pos))
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(400)
                    shot = tmp / f"{file}-{theme}.png"
                    page.screenshot(path=str(shot), full_page=True)
                    page.close()
                    full = Image.open(shot).convert("RGB")
                    for part, (x, y) in maps:
                        full.paste(Image.open(part).convert("RGB"), (round(x), round(y)))
                    pages.append(with_title(full, title, file, theme))
                    print(f"  {theme:5} {file}")
                ctx.close()
                pdf = OUT / f"Plaksha-Website-{theme.capitalize()}-Desktop.pdf"
                pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=96, quality=88)
                print("saved", pdf.relative_to(ROOT))
            browser.close()
    finally:
        httpd.shutdown()
        for f in tmp.glob("*.png"):
            f.unlink()
        tmp.rmdir()


if __name__ == "__main__":
    main()
