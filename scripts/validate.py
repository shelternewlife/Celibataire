import json
import pathlib
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
GA_MEASUREMENT_ID = APP["ga4_measurement_id"]
SCREENSHOTS = json.loads((ROOT / "content/screenshots.json").read_text(encoding="utf-8"))
FEATURES = json.loads((ROOT / "content/features.json").read_text(encoding="utf-8"))
BASE = APP["website_url"].rstrip("/")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
ERRORS = []

class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.canonical = None
        self.hreflang = {}
        self.title = []
        self.h1 = []
        self.in_title = False
        self.in_h1 = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag == "link":
            if attrs.get("rel") == "canonical":
                self.canonical = attrs.get("href")
            if attrs.get("rel") == "alternate" and attrs.get("hreflang"):
                self.hreflang[attrs["hreflang"]] = attrs.get("href")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 = True
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.in_h1:
            self.h1.append(data)

def expected_url(lang, section="home"):
    return f"{BASE}/{lang}/" + ("" if section == "home" else f"{section}/")

def page_path(lang, section="home"):
    return DIST / lang / ("" if section == "home" else section) / "index.html"

def fail(message):
    ERRORS.append(message)

required_files = [
    DIST / "index.html", DIST / "robots.txt", DIST / "sitemap.xml",
    DIST / "llms.txt", DIST / "assets/style.css",
    DIST / "assets/screens/screen-1.webp",
]
if not (ROOT / "content/screenshots.json").is_file():
    fail("Missing source screenshot manifest: content/screenshots.json")
for path in required_files:
    if not path.is_file():
        fail(f"Missing generated file: {path.relative_to(DIST)}")

route_urls = {f"{BASE}/"}
for lang in ("en", "ar"):
    for section in ("home", "about", "features", "download", "faq"):
        route_urls.add(expected_url(lang, section))
        path = page_path(lang, section)
        if not path.is_file():
            fail(f"Missing route: {path.relative_to(DIST)}")
            continue
        parser = DocumentParser()
        parser.feed(path.read_text(encoding="utf-8"))
        expected_canonical = expected_url(lang, section)
        if parser.canonical != expected_canonical:
            fail(f"Wrong canonical for {path.relative_to(DIST)}: {parser.canonical}")
        if parser.hreflang.get("en") != expected_url("en", section):
            fail(f"Wrong English hreflang for {path.relative_to(DIST)}")
        if parser.hreflang.get("ar") != expected_url("ar", section):
            fail(f"Wrong Arabic hreflang for {path.relative_to(DIST)}")
        if parser.hreflang.get("x-default") != expected_url("en", section):
            fail(f"Wrong x-default hreflang for {path.relative_to(DIST)}")
        page_html = path.read_text(encoding="utf-8")
        if f"https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}" not in page_html:
            fail(f"Missing GA4 library on {path.relative_to(DIST)}")
        if f"gtag('config', '{GA_MEASUREMENT_ID}')" not in page_html:
            fail(f"Missing GA4 configuration on {path.relative_to(DIST)}")
        if "gtag('event', 'google_play_click'" not in page_html:
            fail(f"Missing Google Play click event handler on {path.relative_to(DIST)}")
        for required_meta in ('name="description"', 'name="robots" content="index,follow', 'property="og:title"', 'property="og:image"', 'name="twitter:card"'):
            if required_meta not in page_html:
                fail(f"Missing SEO metadata {required_meta} in {path.relative_to(DIST)}")
        if not parser.title or not "".join(parser.title).strip():
            fail(f"Missing title for {path.relative_to(DIST)}")
        if not parser.h1 or not "".join(parser.h1).strip():
            fail(f"Missing H1 for {path.relative_to(DIST)}")
        import re
        tracked_locations = {
            "home": ["home_hero"],
            "about": ["about_intro"],
            "features": ["features_end"],
            "download": ["download_hero", "download_end"],
            "faq": [],
        }
        found_locations = re.findall(r'data-analytics-event="google_play_click" data-cta-location="([^"]+)"', page_html)
        if found_locations != tracked_locations[section]:
            fail(f"Incorrect Google Play click tracking locations on {path.relative_to(DIST)}")
        if section == "download":
            page_html = path.read_text(encoding="utf-8")
            if APP["google_play_url"] not in parser.links:
                fail(f"Download page is missing its official Google Play CTA: {path.relative_to(DIST)}")
            if 'name="description"' not in page_html or 'name="robots" content="index,follow' not in page_html:
                fail(f"Download page is missing SEO description or index directive: {path.relative_to(DIST)}")
            if '"@type": "MobileApplication"' not in page_html or '"installUrl":' not in page_html:
                fail(f"Download page is missing MobileApplication install structured data: {path.relative_to(DIST)}")
        if section == "features":
            page_html = path.read_text(encoding="utf-8")
            if APP["google_play_url"] not in parser.links:
                fail(f"Features page is missing its Google Play CTA: {path.relative_to(DIST)}")
            if len(parser.images) != len(FEATURES):
                fail(f"Features page should illustrate every feature with a screenshot: {path.relative_to(DIST)}")
        if section == "home":
            if len(parser.images) != 1 + (len(SCREENSHOTS) * 2):
                fail(f"Homepage should contain a hero image, {len(SCREENSHOTS)} gallery images and {len(SCREENSHOTS)} feature images: {path.relative_to(DIST)}")
            gallery_images = parser.images[1:1 + len(SCREENSHOTS)]
            if len({image.get("src") for image in gallery_images}) != len(SCREENSHOTS):
                fail(f"Homepage gallery contains duplicate screenshot sources: {path.relative_to(DIST)}")
            if any(not image.get("alt", "").strip() for image in gallery_images):
                fail(f"Homepage gallery contains an image without alt text: {path.relative_to(DIST)}")
        for href in parser.links:
            if href.startswith(("mailto:", "tel:", "#")):
                continue
            parsed = urlparse(href)
            base_parts = urlparse(BASE)
            if parsed.scheme in ("http", "https"):
                if parsed.netloc != base_parts.netloc:
                    continue
                base_path = base_parts.path.rstrip("/")
                if parsed.path != base_path and not parsed.path.startswith(base_path + "/"):
                    fail(f"Internal link escapes project base path: {href} in {path.relative_to(DIST)}")
                    continue
                relative = parsed.path[len(base_path):].lstrip("/")
            else:
                if parsed.scheme or parsed.netloc:
                    fail(f"Unsupported internal link {href} in {path.relative_to(DIST)}")
                    continue
                if not href.startswith(BASE + "/"):
                    fail(f"Internal link escapes project base path: {href} in {path.relative_to(DIST)}")
                    continue
                relative = href[len(BASE) + 1:]
            target = DIST / relative
            if relative.endswith("/"):
                target = target / "index.html"
            elif not target.suffix:
                target = target / "index.html"
            if not target.is_file():
                fail(f"Broken internal link {href} in {path.relative_to(DIST)}")

root_parser = DocumentParser()
if (DIST / "index.html").is_file():
    root_html = (DIST / "index.html").read_text(encoding="utf-8")
    root_parser.feed(root_html)
    if root_parser.canonical != f"{BASE}/":
        fail("Root canonical URL is incorrect")
    if 'name="google-site-verification"' not in root_html:
        fail("Google Search Console verification meta tag missing from root page")
    if f"https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}" not in root_html:
        fail("GA4 library missing from language root")
    if f"gtag('config', '{GA_MEASUREMENT_ID}')" not in root_html:
        fail("GA4 configuration missing from language root")
    for lang in ("en", "ar"):
        if expected_url(lang) not in root_html:
            fail(f"Root language link missing: {lang}")

try:
    sitemap_root = ET.parse(DIST / "sitemap.xml").getroot()
    sitemap_urls = [node.find(f"{NS}loc").text for node in sitemap_root.findall(f"{NS}url")]
    if len(sitemap_urls) != len(route_urls):
        fail(f"Sitemap should contain {len(route_urls)} routes, found {len(sitemap_urls)}")
    if len(set(sitemap_urls)) != len(sitemap_urls):
        fail("Sitemap contains duplicate URLs")
    if set(sitemap_urls) != route_urls:
        fail("Sitemap URLs do not match the generated site routes")
except Exception as exc:
    fail(f"Invalid sitemap XML: {exc}")

robots = (DIST / "robots.txt").read_text(encoding="utf-8") if (DIST / "robots.txt").is_file() else ""
if f"Sitemap: {BASE}/sitemap.xml" not in robots:
    fail("robots.txt does not reference the generated sitemap")

if APP["package_id"] not in APP["google_play_url"]:
    fail("Package ID mismatch in Google Play URL")
if len(SCREENSHOTS) != 5 or any(urlparse(item.get("src", "")).hostname != "play-lh.googleusercontent.com" for item in SCREENSHOTS):
    fail("Gallery must use the five official Google Play screenshot assets")

if ERRORS:
    print("\n".join(ERRORS))
    sys.exit(1)
print(f"Validated {len(route_urls)} routes, navigation targets, canonical/hreflang pairs, root verification and sitemap.")
