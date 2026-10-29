#!/usr/bin/env python3
"""Link-preview cards (og:image / twitter:image, 1200x630) for alecmeeker.com, one per page: the page's title in the
site's type (Newsreader, JetBrains Mono) on a white page, so a shared link shows what the page is, not a photo.
Writes assets/previews/cards/<name>.png and sets each page's og:image and twitter:image to its card.
Needs Playwright (Chromium) and network for the Google fonts. Run from the site root:
    python assets/previews/cards/make_cards.py
"""
import html
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "previews", "cards")
BASE = "https://alecmeeker.com/assets/previews/cards/"
PAPER = "deterministic-first-fact-checking-of-local-news-against-multilingual-sources"

# page -> (card name, label, title, subtitle)
CARDS = {
    f"{PAPER}/index.html": ("factcheck-paper", "Research paper",
                            "Deterministic-First Fact-Checking of Local News Against Multilingual Sources",
                            "A Pre-Registered Evaluation on Held-Out Articles"),
    "verification-desk.html": ("verification-desk", "Research paper",
                               "Deterministic Quotation Verification and a Reduced False-Positive Rate in an "
                               "Automated Source-Fidelity Checker for News", ""),
    "verification-layer.html": ("verification-layer", "Brief", "A Verification Layer for AI Agents", ""),
    "white_paper.html": ("white-paper", "White paper", "Building an AI-Powered Local Newsroom", ""),
    "data_warehouse_report.html": ("data-warehouse", "Report", "Data Warehouse & Ingestion Pipeline", ""),
    "email_assistant_report.html": ("email-assistant", "Report", "Email Assistant", ""),
    "news_scanner_report.html": ("news-scanner", "Report", "NYCNewsScanner & Publisher", ""),
    "email_warehouse_oss.html": ("email-warehouse", "Open source", "Email Ingestion Data Warehouse", ""),
    "multiverse_platform_oss.html": ("multiverse", "Open source", "Local News Multiverse Agent Platform", ""),
    "work.html": ("work", "Published work", "Published Work",
                  "A white paper, subsystem reports, open-source platforms and vidtranscript"),
    "cv.html": ("cv", "CV", "The Record",
                "Founder & CEO, Brooklyn New Media · Owner & Publisher, Bushwick Daily"),
    "index.html": ("home", "Publisher", "Alec Meeker",
                   "Owner and operator of New York media properties. Private consulting in applied AI and communications."),
}

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..700&family=JetBrains+Mono:wght@400;500&display=block" rel="stylesheet">
<style>
:root {{ --paper:#f8f6f1; --ink:#15120e; --muted:#6b645a; --rule:#d9d3c7; --accent:#a8361e; }}
* {{ margin:0; box-sizing:border-box; }}
html, body {{ width:1200px; height:630px; background:var(--paper); }}
body {{ position:relative; padding:64px 88px 56px; color:var(--ink); display:flex; flex-direction:column; }}
body::before {{ content:""; position:absolute; inset:22px; border:1px solid var(--rule); pointer-events:none; }}
.top {{ display:flex; justify-content:space-between; align-items:baseline;
        font:500 17px/1 "JetBrains Mono", monospace; letter-spacing:.2em; text-transform:uppercase; }}
.name {{ padding-bottom:12px; border-bottom:3px solid var(--accent); }}
.label {{ color:var(--muted); font-weight:400; }}
.main {{ flex:1; display:flex; flex-direction:column; justify-content:center; padding:8px 0 0; }}
h1 {{ font-family:"Newsreader", Georgia, serif; font-optical-sizing:auto; font-weight:560; font-size:{size}px;
      line-height:1.06; letter-spacing:-.012em; max-width:1000px; text-wrap:balance; }}
.sub {{ margin-top:22px; font:italic 400 31px/1.25 "Newsreader", Georgia, serif; color:var(--muted); max-width:980px;
        text-wrap:balance; }}
.foot {{ display:flex; justify-content:space-between; align-items:baseline; padding-top:20px; border-top:1px solid var(--rule);
         font:400 16px/1 "JetBrains Mono", monospace; letter-spacing:.14em; color:var(--muted); }}
</style></head><body>
<div class="top"><span class="name">Alec Meeker</span><span class="label">{label}</span></div>
<div class="main"><h1>{title}</h1>{sub}</div>
<div class="foot"><span>alecmeeker.com</span><span>Brooklyn, New York</span></div>
</body></html>"""


def size_for(title, sub):
    n = len(title)
    s = 92 if n <= 22 else 78 if n <= 40 else 66 if n <= 70 else 56 if n <= 100 else 50
    return s - (6 if sub and n > 40 else 0)


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for page, (name, label, title, sub) in CARDS.items():
            doc = TEMPLATE.format(size=size_for(title, sub), label=html.escape(label), title=html.escape(title),
                                  sub=f'<p class="sub">{html.escape(sub)}</p>' if sub else "")
            pg.set_content(doc, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=os.path.join(OUT, f"{name}.png"), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        b.close()


def tag(page_html, prop, attr, value):
    """Set <meta {attr}="{prop}" content="..."> in the head, replacing an existing one or adding it."""
    rx = re.compile(rf'<meta\s+{attr}="{re.escape(prop)}"\s+content="[^"]*"\s*/?>|<meta\s+content="[^"]*"\s+{attr}="{re.escape(prop)}"\s*/?>')
    new = f'<meta {attr}="{prop}" content="{value}">'
    if rx.search(page_html):
        return rx.sub(new, page_html, count=1)
    return page_html.replace("</head>", new + "\n</head>", 1)


def point_pages():
    for page, (name, _l, title, _s) in CARDS.items():
        path = os.path.join(ROOT, page)
        s = open(path, encoding="utf-8").read()
        url = BASE + name + ".png"
        for prop, attr, val in (("og:image", "property", url), ("og:image:width", "property", "1200"),
                                ("og:image:height", "property", "630"), ("og:image:alt", "property", html.escape(title)),
                                ("twitter:card", "name", "summary_large_image"), ("twitter:image", "name", url)):
            s = tag(s, prop, attr, val)
        open(path, "w", encoding="utf-8").write(s)
        print(f"{page}: {url}")


if __name__ == "__main__":
    render()
    point_pages()
