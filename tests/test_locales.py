import json
import re
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
        self.title = ""
        self.description = None
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs.get("hreflang")] = attrs.get("href")
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data

class MarketLocaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)

    def test_locale_titles_and_descriptions_are_localized_and_within_snippet_bounds(self):
        for locale in STRATEGY["published_locales"]:
            bundle = json.loads((ROOT / "content/locales.json").read_text(encoding="utf-8"))[locale]
            observed_titles = set()
            for section in ("", "about", "features", "download", "faq"):
                path = DIST / locale.lower() / section / "index.html" if section else DIST / locale.lower() / "index.html"
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                key = section or "home"
                self.assertEqual(parser.title, bundle["titles"][key], f"{locale}/{key} title")
                self.assertEqual(parser.description, bundle["descriptions"][key], f"{locale}/{key} description")
                self.assertLessEqual(len(parser.title), 60, f"{locale}/{key} title too long")
                self.assertLessEqual(len(parser.description), 160, f"{locale}/{key} description too long")
                self.assertNotIn(parser.title, observed_titles, f"Duplicate title in {locale}")
                observed_titles.add(parser.title)

    def test_market_keyword_clusters_are_relevant_and_avoid_unverified_promises(self):
        clusters = STRATEGY["initial_keyword_clusters"]
        expected = set(STRATEGY["published_locales"])
        self.assertEqual(set(clusters), expected)
        for locale, config in clusters.items():
            self.assertTrue(config["primary"])
            self.assertTrue(config["secondary"])
            self.assertTrue(config["clusters"])
            self.assertTrue(all(item["primary"] for item in config["clusters"]))
            bundle = json.loads((ROOT / "content/locales.json").read_text(encoding="utf-8"))[locale]
            metadata = " ".join(bundle["titles"].values()) + " " + " ".join(bundle["descriptions"].values())
            folded = metadata.casefold()
            for term in config["excluded_terms"]:
                self.assertNotIn(term.casefold(), folded, f"Unsupported keyword claim in {locale}: {term}")
        self.assertIn("job search app", " ".join(clusters["en-US"]["primary"]))
        self.assertIn("job search app Canada", " ".join(clusters["en-CA"]["primary"]))
        self.assertIn("application de recherche d’emploi", " ".join(clusters["fr-CA"]["primary"]))

    def test_only_explicitly_published_locales_are_generated(self):
        expected = {x.lower() for x in STRATEGY["published_locales"]}
        bundle_locales = json.loads((ROOT / "content/locales.json").read_text(encoding="utf-8"))
        self.assertEqual(expected, {x.lower() for x in bundle_locales})
        for locale in expected:
            self.assertTrue((DIST / locale / "index.html").is_file())
        for locale in ("nl-nl", "pl-pl", "en-gb"):
            self.assertFalse((DIST / locale).exists(), f"Unpublished locale was generated: {locale}")

    def test_all_core_routes_exist_and_have_self_canonical(self):
        for locale in STRATEGY["published_locales"]:
            slug = locale.lower()
            for section in ("", "about", "features", "download", "faq"):
                path = DIST / slug / (section or "") / "index.html"
                self.assertTrue(path.is_file(), f"Missing {locale}/{section}")
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                expected = f"{BASE}/{slug}/" + ("" if not section else f"{section}/")
                self.assertEqual(parser.canonical, expected)

    def test_hreflang_is_complete_and_reciprocal_for_every_equivalent_page(self):
        expected_locales = set(STRATEGY["published_locales"])
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
        for locale in STRATEGY["published_locales"]:
            source = (DIST / locale.lower() / "index.html").read_text(encoding="utf-8")
            parser = Links()
            parser.feed(source)
            for target in {x.lower() for x in STRATEGY["published_locales"]}:
                self.assertTrue(
                    any(link.startswith(f"{BASE}/{target}/") for link in parser.links),
                    f"{locale} has no flag link for {target}",
                )
            self.assertNotIn(f"{BASE}/ar/", parser.links)
            self.assertNotIn(f"{BASE}/en/", parser.links)

    def test_french_pages_have_genuine_french_content_and_metadata(self):
        for locale in ("fr-CA", "fr-FR"):
            source = (DIST / locale.lower() / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'<html lang="{locale}"', source)
            self.assertIn("Découvrez", source)
            self.assertIn("Application de recherche d’emploi", source)
            self.assertIn("Foire aux questions", (DIST / locale.lower() / "faq" / "index.html").read_text(encoding="utf-8"))
            self.assertNotIn("Discover your next opportunity", source)
            self.assertNotIn("Frequently asked questions", source)

    def test_localized_feature_detail_routes_are_real_and_reciprocal(self):
        from scripts.build import FEATURES
        for locale in STRATEGY["published_locales"]:
            slug = locale.lower()
            for feature in FEATURES:
                tail = f"features/{feature['id']}/"
                path = DIST / slug / tail / "index.html"
                self.assertTrue(path.is_file(), f"Missing {locale}/{tail}")
                parser = Links()
                parser.feed(path.read_text(encoding="utf-8"))
                self.assertEqual(parser.canonical, f"{BASE}/{slug}/{tail}")
                self.assertEqual(parser.alternates, {
                    **{code: f"{BASE}/{code.lower()}/{tail}" for code in STRATEGY["published_locales"]},
                    "x-default": f"{BASE}/en-us/{tail}",
                })

    def test_sitemaps_contain_exactly_published_locale_routes(self):
        from scripts.build import FEATURES
        expected = {
            f"{BASE}/{locale.lower()}/{tail}"
            for locale in STRATEGY["published_locales"]
            for tail in ("", "about/", "features/", "download/", "faq/")
        }
        expected.update(
            f"{BASE}/{locale.lower()}/features/{feature['id']}/"
            for locale in STRATEGY["published_locales"] for feature in FEATURES
        )
        xml_root = ET.parse(DIST / "sitemap.xml").getroot()
        entries = xml_root.findall(f"{NS}url")
        xml_urls = {node.findtext(f"{NS}loc") for node in entries}
        text_urls = set((DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines())
        self.assertTrue(expected.issubset(xml_urls))
        self.assertTrue(expected.issubset(text_urls))
        self.assertEqual(len(xml_urls), len(entries))
        self.assertEqual(len(text_urls), len((DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines()))
        for locale in ("nl-NL", "pl-PL", "en-GB"):
            self.assertFalse(any(f"/{locale.lower()}/" in url for url in xml_urls | text_urls))

    def test_sitemap_hreflang_reciprocity(self):
        root = ET.parse(DIST / "sitemap.xml").getroot()
        expected_locales = set(STRATEGY["published_locales"])
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

    def test_flag_only_locale_switcher_is_top_left_and_above_navigation(self):
        expected_flags = {
            "en-US": "🇺🇸", "en-CA": "🇨🇦", "fr-CA": "🇨🇦",
            "es-ES": "🇪🇸", "pt-PT": "🇵🇹", "fr-FR": "🇫🇷",
            "de-DE": "🇩🇪", "it-IT": "🇮🇹",
        }
        for locale in STRATEGY["published_locales"]:
            source = (DIST / locale.lower() / "index.html").read_text(encoding="utf-8")
            switch = re.search(r'<div class="locale-switch"[^>]*>(.*?)</div>', source, re.DOTALL)
            self.assertIsNotNone(switch, locale)
            header = source.index("<header>")
            switch_pos = source.index('<div class="locale-switch"')
            nav_pos = source.index('<nav aria-label="Primary navigation">')
            self.assertLess(header, switch_pos)
            self.assertLess(switch_pos, nav_pos)
            for code, flag in expected_flags.items():
                self.assertIn(f'lang="{code}"', switch.group(1), f"{locale} missing {code}")
                self.assertIn(f'<span aria-hidden="true">{flag}</span>', switch.group(1))
            self.assertNotRegex(switch.group(1), r'>\s*(?:US English|English \(Canada\)|Français|Español|Português|Deutsch|Italiano)')
        root = (DIST / "index.html").read_text(encoding="utf-8")
        root_switch = re.search(r'<div class="locale-switch"[^>]*>(.*?)</div>', root, re.DOTALL)
        self.assertIsNotNone(root_switch)
        for code in expected_flags:
            self.assertIn(f'lang="{code}"', root_switch.group(1))
        for legacy in ("en", "ar"):
            page = (DIST / legacy / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="locale-switch"', page)
            for code in expected_flags:
                self.assertIn(f'lang="{code}"', page)

    def test_root_selector_points_to_every_published_locale(self):
        source = (DIST / "index.html").read_text(encoding="utf-8")
        for locale in STRATEGY["published_locales"]:
            self.assertIn(f'hreflang="{locale}"', source)
            self.assertIn(f'href="{BASE}/{locale.lower()}/"', source)
        self.assertIn(f'hreflang="x-default" href="{BASE}/"', source)

if __name__ == "__main__":
    unittest.main()
