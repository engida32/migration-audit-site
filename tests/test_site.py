import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site" if (ROOT / "site").is_dir() else ROOT
PAGES = ["index.html", "sample.html", "pricing.html", "about.html"]
ALL_PAGES = PAGES + ["404.html"]
BASE = "https://engida32.github.io/migration-audit-site/"
BANNED = ["supercharge", "unlock", "revolutionize", "game-changer", "seamless",
          "cutting-edge", "delve", "empower", "leverage", "synergy"]
PALETTE = ("#f7f4ec", "#171512", "#a83a0f", "#d9d2c3", "#4a453d")
CTA = "mailto:engida32lishan@gmail.com"


class Doc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.links = []
        self.mailto = False
        self.title = False
        self.scripts = []
        self.refs = []
        self.stylesheets = []
        self.icons = []
        self.descriptions = []
        self.aria_current = 0
        self.mains = []
        self.tables = 0
        self.captions = 0
        self.scope_cols = 0
        self.table_wraps = 0
        self.cells = 0
        self.labelled_cells = 0
        self.canonicals = []
        self.og = {}
        self.twitter = {}
        self.robots = []
        self.details = 0
        self.base = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title = True
        if tag == "script":
            self.scripts.append(attrs.get("type"))
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if attrs["href"].startswith("mailto:"):
                self.mailto = True
            self.refs.append(attrs["href"])
        if tag == "link" and attrs.get("href"):
            rel = attrs.get("rel", "")
            if rel == "stylesheet":
                self.stylesheets.append(attrs["href"])
            if rel == "canonical":
                self.canonicals.append(attrs["href"])
            if rel in ("icon", "apple-touch-icon"):
                self.icons.append(attrs["href"])
            if rel in ("stylesheet", "icon", "apple-touch-icon", "preload"):
                self.refs.append(attrs["href"])
        if tag == "img" and attrs.get("src"):
            self.refs.append(attrs["src"])
        if tag == "meta":
            name = attrs.get("name")
            prop = attrs.get("property")
            if name == "description":
                self.descriptions.append(attrs.get("content", ""))
            if name == "robots":
                self.robots.append(attrs.get("content", ""))
            if prop and prop.startswith("og:"):
                self.og[prop] = attrs.get("content", "")
            if name and name.startswith("twitter:"):
                self.twitter[name] = attrs.get("content", "")
        if attrs.get("aria-current") == "page":
            self.aria_current += 1
        if tag == "main":
            self.mains.append(attrs.get("id"))
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1
        if attrs.get("scope") == "col":
            self.scope_cols += 1
        if "table-wrap" in attrs.get("class", "").split():
            self.table_wraps += 1
        if tag == "td":
            self.cells += 1
            if attrs.get("data-label"):
                self.labelled_cells += 1
        if tag == "details":
            self.details += 1
        if tag == "base":
            self.base = attrs.get("href")


def parse(name):
    doc = Doc()
    doc.feed((SITE / name).read_text(encoding="utf-8"))
    return doc


def text(name):
    return (SITE / name).read_text(encoding="utf-8")


def json_ld(name):
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        text(name), re.S | re.I,
    )
    return [json.loads(block) for block in blocks]


def ld_types(value):
    found = set()
    if isinstance(value, dict):
        item = value.get("@type")
        if isinstance(item, str):
            found.add(item)
        elif isinstance(item, list):
            found.update(item)
        for child in value.values():
            found |= ld_types(child)
    elif isinstance(value, list):
        for child in value:
            found |= ld_types(child)
    return found


def test_every_page_has_one_h1_and_title():
    for name in ALL_PAGES:
        doc = parse(name)
        assert doc.h1 == 1, name
        assert doc.title, name


def test_titles_and_descriptions_are_unique():
    titles = [re.search(r"<title>(.*?)</title>", text(name), re.S).group(1).strip()
              for name in ALL_PAGES]
    descriptions = [parse(name).descriptions[0] for name in ALL_PAGES]
    assert len(set(titles)) == len(ALL_PAGES)
    assert len(set(descriptions)) == len(ALL_PAGES)


def test_internal_links_resolve():
    for name in ALL_PAGES:
        for href in parse(name).links:
            if href.startswith(("http", "mailto:", "#")):
                continue
            target = (SITE / href.split("#")[0]).resolve()
            assert target.is_file(), f"{name} -> {href}"


def test_cta_address_on_every_page():
    for name in ALL_PAGES:
        assert CTA in text(name), name


def test_no_banned_copy():
    copy = " ".join(text(name).lower() for name in ALL_PAGES)
    for word in BANNED:
        assert word not in copy, word


def test_palette_is_complete():
    css = (SITE / "assets" / "site.css").read_text(encoding="utf-8").lower()
    for color in PALETTE:
        assert color in css, color


def test_stylesheets_resolve():
    for name in ALL_PAGES:
        doc = parse(name)
        assert doc.stylesheets, name
        for href in doc.stylesheets:
            assert (SITE / href).is_file(), f"{name} -> {href}"


def test_favicon_resolves():
    for name in ALL_PAGES:
        doc = parse(name)
        assert doc.icons, name
        for href in doc.icons:
            assert (SITE / href).is_file(), f"{name} -> {href}"


def test_no_executable_scripts_or_external_assets():
    for name in ALL_PAGES:
        doc = parse(name)
        for kind in doc.scripts:
            assert kind == "application/ld+json", f"{name} -> {kind}"
        for ref in doc.refs:
            assert not ref.startswith(("http://", "https://")), f"{name} -> {ref}"


def test_font_faces_resolve_to_real_woff2_files():
    css = (SITE / "assets" / "site.css").read_text(encoding="utf-8")
    faces = re.findall(r"@font-face\s*\{(.*?)\}", css, re.S | re.I)
    assert len(faces) == 5
    urls = []
    for face in faces:
        assert "font-display: swap" in face.lower()
        found = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', face)
        assert len(found) == 1, face
        urls.extend(found)
    assert len(set(urls)) == 5
    for url in urls:
        assert url.startswith("fonts/"), url
        target = (SITE / "assets" / url).resolve()
        assert target.is_file(), url
        assert target.stat().st_size > 0, url
        assert target.read_bytes()[:4] == b"wOF2", url
    assert (SITE / "assets" / "fonts" / "OFL.txt").is_file()


def test_sample_contains_reviewed_findings():
    sample = text("sample.html")
    for token in ("F-004", "F-009", "148 passed"):
        assert token in sample, token


def test_current_pricing_replaces_old_pricing():
    pricing = text("pricing.html")
    for token in ("$650", "$1,050", "$125", "5 business days"):
        assert token in pricing, token
    for old in ("$750", "$1,200", "$150"):
        assert old not in pricing, old
    assert "From $650" in text("index.html")


def test_seo_metadata_and_canonicals():
    for name in PAGES:
        doc = parse(name)
        expected = BASE if name == "index.html" else BASE + name
        assert doc.canonicals == [expected], name
        assert doc.og.get("og:title"), name
        assert doc.og.get("og:description"), name
        assert doc.og.get("og:url") == expected, name
        assert doc.og.get("og:type") == "website", name
        assert doc.og.get("og:image") == BASE + "assets/og-card.png", name
        assert doc.twitter.get("twitter:card") == "summary_large_image", name
        assert doc.twitter.get("twitter:title"), name
        assert doc.twitter.get("twitter:description"), name
        assert doc.twitter.get("twitter:image") == BASE + "assets/og-card.png", name
        blocks = json_ld(name)
        assert blocks, name
        assert "ProfessionalService" in set().union(*(ld_types(block) for block in blocks)), name


def ld_find(value, type_name):
    if isinstance(value, dict):
        direct = value.get("@type")
        direct = {direct} if isinstance(direct, str) else set(direct or [])
        if type_name in direct:
            return value
        for child in value.values():
            found = ld_find(child, type_name)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = ld_find(child, type_name)
            if found:
                return found
    return None


def test_faq_is_visible_and_marked_up():
    doc = parse("index.html")
    assert doc.details >= 5
    questions = [unescape(re.sub(r"<[^>]+>", "", item)).strip()
                 for item in re.findall(r"<summary>(.*?)</summary>", text("index.html"), re.S)]
    assert len(questions) >= 5
    faq = ld_find(json_ld("index.html"), "FAQPage")
    assert faq
    names = [item["name"] for item in faq["mainEntity"]]
    assert len(names) >= 5
    for question in questions:
        assert question in names, question


def test_robots_and_sitemap():
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: " + BASE + "sitemap.xml" in robots
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    expected = [BASE if name == "index.html" else BASE + name for name in PAGES]
    assert locs == expected
    assert "404" not in sitemap


def test_404_is_real_and_noindex():
    doc = parse("404.html")
    assert doc.robots and "noindex" in doc.robots[0]
    assert not doc.canonicals
    assert 'href="index.html"' in text("404.html")


def test_404_assets_resolve_from_deep_paths():
    doc = parse("404.html")
    assert doc.base == "/migration-audit-site/"
    for ref in doc.refs:
        if ref.startswith(("mailto:", "#")):
            continue
        assert not ref.startswith(("http://", "https://")), ref
        joined = doc.base + ref
        target = (SITE / joined[len(doc.base):]).resolve()
        assert target.is_file(), ref


def test_social_card_is_a_real_png():
    card = SITE / "assets" / "og-card.png"
    assert card.is_file()
    assert card.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert card.stat().st_size > 10_000


def test_accessibility_scaffolding():
    descriptions = set()
    for name in ALL_PAGES:
        page = text(name)
        doc = parse(name)
        assert re.search(r'<body>\s*<a class="skip" href="#main">Skip to content</a>', page), name
        assert doc.mains == ["main"], name
        assert doc.aria_current == (0 if name == "404.html" else 1), name
        assert len(doc.descriptions) == 1 and doc.descriptions[0], name
        descriptions.add(doc.descriptions[0])
        assert doc.table_wraps == doc.tables, name
        assert doc.captions == doc.tables, name
        assert doc.cells == doc.labelled_cells, name
        if doc.tables:
            assert doc.scope_cols >= doc.tables, name
        footer = re.search(r"<footer>.*?</footer>", page, re.S)
        assert footer and CTA in footer.group(0), name
    assert len(descriptions) == len(ALL_PAGES)


def test_design_system_constraints():
    css = (SITE / "assets" / "site.css").read_text(encoding="utf-8").lower()
    assert "--paper: #f7f4ec" in css
    assert "--ink: #171512" in css
    assert "--accent: #a83a0f" in css
    assert "--muted: #4a453d" in css
    assert "repeat(12" in css
    assert "font-weight: 600" in css
    assert "max-width: 68ch" in css
    assert "@media (max-width: 760px)" in css
    assert "attr(data-label)" in css
    assert "prefers-reduced-motion" in css
