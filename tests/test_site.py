import json
import pathlib
import subprocess
import sys
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
BASE = APP["website_url"].rstrip("/")

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.h1 = []
        self.in_h1 = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag == "h1":
            self.in_h1 = True
    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_h1 = False
    def handle_data(self, data):
        if self.in_h1:
            self.h1.append(data)

def output_path(lang, section="home"):
    return DIST / lang / ("" if section == "home" else section) / "index.html"

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)

    def test_google_site_verification_tag(self):
        source = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="google-site-verification"', source)
        self.assertIn("8mOiNMu4Tn477yFaR-IWrNQGhdqH1TpF6NKKoN94Oms", source)

    def test_identity_and_store_url(self):
        self.assertEqual(APP["name"], "Job Connect")
        self.assertIn(APP["package_id"], APP["google_play_url"])

    def test_all_expected_routes_exist(self):
        self.assertTrue((DIST / "index.html").is_file())
        for lang in ("en", "ar"):
            for section in ("home", "about", "features", "download", "faq"):
                self.assertTrue(output_path(lang, section).is_file(), f"{lang}/{section}")

    def test_page_content_is_section_specific(self):
        expected = {
            "en": {"about": "About Job Connect", "features": "Explore the features", "faq": "Frequently asked questions"},
            "ar": {"about": "عن Job Connect", "features": "استكشف المزايا", "faq": "الأسئلة الشائعة"},
        }
        for lang in ("en", "ar"):
            headings = []
            for section in ("about", "features", "faq"):
                parser = PageParser()
                parser.feed(output_path(lang, section).read_text(encoding="utf-8"))
                heading = "".join(parser.h1).strip()
                self.assertIn(expected[lang][section], heading)
                headings.append(heading)
            self.assertEqual(len(set(headings)), 3, f"Duplicate page headings for {lang}")

    def test_navigation_uses_project_root_urls(self):
        for lang in ("en", "ar"):
            for section in ("home", "about", "features", "download", "faq"):
                parser = PageParser()
                parser.feed(output_path(lang, section).read_text(encoding="utf-8"))
                self.assertIn(f"{BASE}/{lang}/about/", parser.links)
                self.assertIn(f"{BASE}/{lang}/features/", parser.links)
                self.assertIn(f"{BASE}/{lang}/faq/", parser.links)
                self.assertIn(f"{BASE}/", parser.links)

    def test_language_switch_preserves_page(self):
        for lang in ("en", "ar"):
            other = "ar" if lang == "en" else "en"
            for section in ("home", "about", "features", "download", "faq"):
                parser = PageParser()
                parser.feed(output_path(lang, section).read_text(encoding="utf-8"))
                expected = f"{BASE}/{other}/" + ("" if section == "home" else f"{section}/")
                self.assertIn(expected, parser.links)

    def test_sitemap_contains_root_and_all_language_routes(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(DIST / "sitemap.xml").getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urls = [node.find(f"{ns}loc").text for node in root.findall(f"{ns}url")]
        self.assertEqual(len(urls), 11)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn(f"{BASE}/", urls)
        for lang in ("en", "ar"):
            for section in ("home", "about", "features", "download", "faq"):
                expected = f"{BASE}/{lang}/" + ("" if section == "home" else f"{section}/")
                self.assertIn(expected, urls)

    def test_root_language_gateway_and_verification(self):
        source = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'href="{BASE}/en/"', source)
        self.assertIn(f'href="{BASE}/ar/"', source)
        self.assertIn(f'<link rel="canonical" href="{BASE}/">', source)

    def test_screenshot_asset_exists(self):
        self.assertTrue((DIST / "assets/screens/screen-1.webp").is_file())

    def test_homepage_uses_five_distinct_google_play_screenshots(self):
        for lang in ("en", "ar"):
            parser = PageParser()
            parser.feed(output_path(lang).read_text(encoding="utf-8"))
            gallery_images = parser.images[1:6]
            self.assertEqual(len(parser.images), 11)
            self.assertEqual(len(gallery_images), 5)
            self.assertEqual(len({image.get("src") for image in gallery_images}), 5)
            self.assertTrue(all(image.get("src", "").startswith("https://play-lh.googleusercontent.com/") for image in gallery_images))
            self.assertTrue(all(image.get("alt", "").strip() for image in gallery_images))
            self.assertIn('id="screenshots"', output_path(lang).read_text(encoding="utf-8"))


    def test_download_pages_have_official_store_cta_and_seo(self):
        for lang in ("en", "ar"):
            source = output_path(lang, "download").read_text(encoding="utf-8")
            parser = PageParser()
            parser.feed(source)
            self.assertIn(APP["google_play_url"], parser.links)
            self.assertIn('rel="canonical"', source)
            self.assertIn('hreflang="ar"', source)
            self.assertIn('hreflang="en"', source)
            self.assertIn('hreflang="x-default"', source)
            self.assertIn('name="description"', source)
            self.assertIn('name="robots" content="index,follow', source)
            self.assertIn('property="og:image"', source)
            self.assertIn('name="twitter:card"', source)
            self.assertIn('"@type": "MobileApplication"', source)
            self.assertIn(APP["package_id"], source)
            self.assertIn("target=\"_blank\"", source)

    def test_features_pages_show_each_feature_and_download_cta(self):
        for lang in ("en", "ar"):
            source = output_path(lang, "features").read_text(encoding="utf-8")
            parser = PageParser()
            parser.feed(source)
            self.assertEqual(len(parser.images), 5)
            self.assertIn(APP["google_play_url"], parser.links)
            self.assertIn('id="feature-discovery"', source)
            self.assertIn('id="feature-collections"', source)

    def test_no_previous_brand(self):
        for path in DIST.rglob("*.html"):
            self.assertNotIn("Mingle", path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
