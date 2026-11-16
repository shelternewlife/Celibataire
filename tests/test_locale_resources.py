import pathlib
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BASE = "https://shelternewlife.github.io/tobemotif-app-discovery"
STRATEGY = __import__("json").loads((ROOT / "content/market-strategy.json").read_text(encoding="utf-8"))
LOCALES = tuple(STRATEGY["published_locales"])
HUBS = ("tips", "blog", "guide", "comparison")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML = "{http://www.w3.org/1999/xhtml}"

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.canonical = None
        self.alternates = {}
        self.title = ""
        self.h1 = 0
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs.get("hreflang")] = attrs.get("href")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1 += 1
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data

class LocalizedResourceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)

    def test_all_four_resource_hubs_exist_for_every_published_locale(self):
        for locale in LOCALES:
            slug = locale.lower()
            for tail in HUBS:
                path = DIST / slug / tail / "index.html"
                self.assertTrue(path.is_file(), f"Missing {locale}/{tail}/")
                source = path.read_text(encoding="utf-8")
                parser = Page()
                parser.feed(source)
                self.assertEqual(parser.canonical, f"{BASE}/{slug}/{tail}/")
                self.assertEqual(parser.h1, 1)
                self.assertIn(f'<html lang="{locale}"', source)
                expected = {
                    code: f"{BASE}/{code.lower()}/{tail}/"
                    for code in LOCALES
                }
                expected["x-default"] = f"{BASE}/en-us/{tail}/"
                self.assertEqual(parser.alternates, expected)

    def test_localized_resource_links_resolve_to_real_pages(self):
        for locale in LOCALES:
            slug = locale.lower()
            for tail in HUBS:
                parser = Page()
                parser.feed((DIST / slug / tail / "index.html").read_text(encoding="utf-8"))
                for href in parser.links:
                    if href.startswith(("mailto:", "tel:", "#")):
                        continue
                    if href.startswith("https://") and not href.startswith(BASE + "/"):
                        continue
                    self.assertTrue(href.startswith(BASE + "/"), href)
                    relative = href[len(BASE) + 1:]
                    target = DIST / relative
                    if relative.endswith("/") or not target.suffix:
                        target = target / "index.html"
                    self.assertTrue(target.is_file(), f"Broken link in {locale}/{tail}: {href}")

    def test_french_hubs_have_french_titles_and_content(self):
        expected_phrases = {
            "tips": "Conseils pour la recherche d’emploi",
            "blog": "Blogue et ressources carrière",
            "guide": "Guide d’utilisation de Job Connect",
            "comparison": "Comparer les méthodes de recherche d’emploi",
        }
        for tail in HUBS:
            source = (DIST / "fr-ca" / tail / "index.html").read_text(encoding="utf-8")
            self.assertIn(expected_phrases[tail], source, tail)
            self.assertNotIn("Job search tips", source, tail)
            self.assertNotIn("User guide", source, tail)
            self.assertIn('og:locale" content="fr_CA"', source)

    def test_sitemaps_include_all_twelve_localized_resource_routes_once(self):
        expected = {
            f"{BASE}/{locale.lower()}/{tail}/"
            for locale in LOCALES for tail in HUBS
        }
        xml_root = ET.parse(DIST / "sitemap.xml").getroot()
        xml_urls = [
            node.findtext(f"{NS}loc")
            for node in xml_root.findall(f"{NS}url")
        ]
        text_urls = [
            line.strip()
            for line in (DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(expected.issubset(set(xml_urls)))
        self.assertTrue(expected.issubset(set(text_urls)))
        self.assertEqual(len(xml_urls), len(set(xml_urls)))
        self.assertEqual(len(text_urls), len(set(text_urls)))
        for node in xml_root.findall(f"{NS}url"):
            loc = node.findtext(f"{NS}loc")
            if loc in expected:
                alternates = {
                    item.get("hreflang"): item.get("href")
                    for item in node.findall(f"{XHTML}link")
                }
                tail = loc.rsplit("/", 2)[-2]
                self.assertEqual(alternates, {
                    **{code: f"{BASE}/{code.lower()}/{tail}/" for code in LOCALES},
                    "x-default": f"{BASE}/en-us/{tail}/"
                })

if __name__ == "__main__":
    unittest.main()
