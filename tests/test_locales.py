import json
import pathlib
import subprocess
import sys
import unittest
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
STRATEGY = json.loads((ROOT / "content/market-strategy.json").read_text(encoding="utf-8"))
BASE = APP["website_url"].rstrip("/")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML = "{http://www.w3.org/1999/xhtml}"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.alternates = {}
        self.canonical = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs.get("hreflang")] = attrs.get("href")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

class MarketLocaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)

    def test_only_explicitly_published_locales_are_generated(self):
        expected = {"en-us", "en-ca", "fr-ca"}
        self.assertEqual({x.lower() for x in STRATEGY["published_locales"]}, expected)
        for locale in expected:
            self.assertTrue((DIST / locale / "index.html").is_file())
        for locale in ("de-de", "fr-fr", "es-es", "nl-nl", "pl-pl"):
            self.assertFalse((DIST / locale).exists(), f"Unpublished locale was generated: {locale}")

    def test_all_core_routes_exist_and_have_self_canonical(self):
        for locale in ("en-US", "en-CA", "fr-CA"):
            slug = locale.lower()
            for section in ("", "about", "features", "download", "faq"):
                path = DIST / slug / (section or "") / "index.html"
                self.assertTrue(path.is_file(), f"Missing {locale}/{section}")
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                expected = f"{BASE}/{slug}/" + ("" if not section else f"{section}/")
                self.assertEqual(parser.canonical, expected)

    def test_hreflang_is_complete_and_reciprocal_for_every_equivalent_page(self):
        expected_locales = {"en-US", "en-CA", "fr-CA"}
        for locale in expected_locales:
            slug = locale.lower()
            for section in ("", "about", "features", "download", "faq"):
                path = DIST / slug / (section or "") / "index.html"
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                tail = "" if not section else f"{section}/"
                expected = {code: f"{BASE}/{code.lower()}/{tail}" for code in expected_locales}
                expected["x-default"] = f"{BASE}/en-us/{tail}"
                self.assertEqual(parser.alternates, expected, f"{locale}/{section}")

    def test_localized_navigation_stays_within_the_market_locale_family(self):
        for locale in ("en-US", "en-CA", "fr-CA"):
            source = (DIST / locale.lower() / "index.html").read_text(encoding="utf-8")
            parser = Links()
            parser.feed(source)
            for target in ("en-us", "en-ca", "fr-ca"):
                self.assertIn(f"{BASE}/{target}/", parser.links)
            self.assertNotIn(f"{BASE}/ar/", parser.links)
            self.assertNotIn(f"{BASE}/en/", parser.links)

    def test_french_page_has_genuine_french_content_and_metadata(self):
        source = (DIST / "fr-ca" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="fr-CA"', source)
        self.assertIn("Découvrez votre prochaine possibilité", source)
        self.assertIn("Application de recherche d’emploi", source)
        self.assertIn("Foire aux questions", (DIST / "fr-ca" / "faq" / "index.html").read_text(encoding="utf-8"))
        self.assertNotIn("Discover your next opportunity", source)
        self.assertNotIn("Frequently asked questions", source)

    def test_localized_feature_detail_routes_are_real_and_reciprocal(self):
        from scripts.build import FEATURES
        for locale in ("en-US", "en-CA", "fr-CA"):
            slug = locale.lower()
            for feature in FEATURES:
                tail = f"features/{feature['id']}/"
                path = DIST / slug / tail / "index.html"
                self.assertTrue(path.is_file(), f"Missing {locale}/{tail}")
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                self.assertEqual(parser.canonical, f"{BASE}/{slug}/{tail}")
                self.assertEqual(parser.alternates, {
                    "en-US": f"{BASE}/en-us/{tail}",
                    "en-CA": f"{BASE}/en-ca/{tail}",
                    "fr-CA": f"{BASE}/fr-ca/{tail}",
                    "x-default": f"{BASE}/en-us/{tail}",
                })

    def test_sitemaps_contain_exactly_published_locale_routes(self):
        from scripts.build import FEATURES
        expected = {
            f"{BASE}/{locale.lower()}/{tail}"
            for locale in ("en-US", "en-CA", "fr-CA")
            for tail in ("", "about/", "features/", "download/", "faq/")
        }
        expected.update(
            f"{BASE}/{locale.lower()}/features/{feature['id']}/"
            for locale in ("en-US", "en-CA", "fr-CA") for feature in FEATURES
        )
        xml_root = ET.parse(DIST / "sitemap.xml").getroot()
        entries = xml_root.findall(f"{NS}url")
        xml_urls = {node.findtext(f"{NS}loc") for node in entries}
        text_urls = set((DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines())
        self.assertTrue(expected.issubset(xml_urls))
        self.assertTrue(expected.issubset(text_urls))
        self.assertEqual(len(xml_urls), len(entries))
        self.assertEqual(len(text_urls), len((DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines()))
        self.assertFalse(any("/de-de/" in url or "/fr-fr/" in url for url in xml_urls | text_urls))

    def test_sitemap_hreflang_reciprocity(self):
        root = ET.parse(DIST / "sitemap.xml").getroot()
        expected_locales = {"en-US", "en-CA", "fr-CA"}
        for node in root.findall(f"{NS}url"):
            loc = node.findtext(f"{NS}loc") or ""
            if not any(f"/{code.lower()}/" in loc for code in expected_locales):
                continue
            base_path = urlparse(BASE).path.rstrip("/") + "/"
            relative = urlparse(loc).path[len(base_path):]
            parts = relative.split("/", 1)
            rest = parts[1] if len(parts) > 1 else ""
            base_tail = rest
            alternates = {item.get("hreflang"): item.get("href") for item in node.findall(f"{XHTML}link")}
            expected = {code: f"{BASE}/{code.lower()}/{base_tail}" for code in expected_locales}
            expected["x-default"] = f"{BASE}/en-us/{base_tail}"
            self.assertEqual(alternates, expected, loc)

    def test_root_selector_points_to_the_three_launch_locales(self):
        source = (DIST / "index.html").read_text(encoding="utf-8")
        for locale in ("en-US", "en-CA", "fr-CA"):
            self.assertIn(f'hreflang="{locale}"', source)
            self.assertIn(f'href="{BASE}/{locale.lower()}/"', source)
        self.assertIn(f'hreflang="x-default" href="{BASE}/"', source)

if __name__ == "__main__":
    unittest.main()
