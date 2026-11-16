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
from scripts.build_resources import routes as resource_routes, DATA, GUIDES

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.tracked_ctas = []
        self.images = []
        self.h1 = []
        self.in_h1 = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if attrs.get("data-analytics-event") == "google_play_click":
                self.tracked_ctas.append(attrs)
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
        self.assertEqual(len(urls), 1 + len(resource_routes()))
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

    def test_sitemap_contains_reciprocal_language_alternates(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(DIST / "sitemap.xml").getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        xhtml = "{http://www.w3.org/1999/xhtml}"
        entries = root.findall(f"{ns}url")
        self.assertEqual(len(entries), 1 + len(resource_routes()))
        for entry in entries:
            loc = entry.find(f"{ns}loc").text
            alternates = {
                node.get("hreflang"): node.get("href")
                for node in entry.findall(f"{xhtml}link")
            }
            if loc == f"{BASE}/":
                self.assertEqual(alternates, {
                    "en": f"{BASE}/en/",
                    "ar": f"{BASE}/ar/",
                    "x-default": f"{BASE}/",
                })
                continue
            route = loc[len(BASE) + 1:].strip("/")
            parts = route.split("/")
            tail = "/".join(parts[1:])
            self.assertEqual(alternates, {
                "en": f"{BASE}/en/" + (f"{tail}/" if tail else ""),
                "ar": f"{BASE}/ar/" + (f"{tail}/" if tail else ""),
                "x-default": f"{BASE}/en/" + (f"{tail}/" if tail else ""),
            })

    def test_robots_txt_references_both_canonical_sitemaps(self):
        lines = [line.strip() for line in (DIST / "robots.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertIn("User-agent: *", lines)
        self.assertIn("Allow: /", lines)
        self.assertEqual([line for line in lines if line.lower().startswith("sitemap:")], [f"Sitemap: {BASE}/sitemap.xml", f"Sitemap: {BASE}/sitemap.txt"])

    def test_text_sitemap_contains_root_and_all_language_routes(self):
        urls = [line.strip() for line in (DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(urls), 1 + len(resource_routes()))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn(f"{BASE}/", urls)
        for lang in ("en", "ar"):
            for section in ("home", "about", "features", "download", "faq"):
                expected = f"{BASE}/{lang}/" + ("" if section == "home" else f"{section}/")
                self.assertIn(expected, urls)

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

    def test_ga4_tracks_google_play_ctas_with_page_context(self):
        measurement_id = APP["ga4_measurement_id"]
        expected_locations = {
            "home": ["home_hero"],
            "about": ["about_intro"],
            "features": ["features_end"],
            "download": ["download_hero", "download_end"],
            "faq": ["faq_end"],
        }
        for lang in ("en", "ar"):
            for section, locations in expected_locations.items():
                source = output_path(lang, section).read_text(encoding="utf-8")
                parser = PageParser()
                parser.feed(source)
                self.assertIn(f"https://www.googletagmanager.com/gtag/js?id={measurement_id}", source)
                self.assertIn(f"gtag('config', '{measurement_id}')", source)
                self.assertIn("gtag('event', 'google_play_click'", source)
                self.assertEqual([cta.get("data-cta-location") for cta in parser.tracked_ctas], locations)
                for cta in parser.tracked_ctas:
                    self.assertEqual(cta.get("href"), APP["google_play_url"])
                    self.assertEqual(cta.get("data-analytics-event"), "google_play_click")
        root = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"gtag('config', '{measurement_id}')", root)

    def test_pages_have_skip_links_and_single_main_heading(self):
        for lang in ("en", "ar"):
            for section in ("home", "about", "features", "download", "faq"):
                source = output_path(lang, section).read_text(encoding="utf-8")
                self.assertIn('<a class="skip-link" href="#main-content">', source)
                self.assertIn('<main id="main-content">', source)
                self.assertEqual(source.count("<h1"), 1)
        root = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a class="skip-link" href="#language-content">', root)
        self.assertIn('<main id="language-content"', root)

    def test_all_images_have_alt_text_and_intrinsic_dimensions(self):
        for path in DIST.rglob("*.html"):
            parser = PageParser()
            parser.feed(path.read_text(encoding="utf-8"))
            for image in parser.images:
                self.assertTrue(image.get("alt", "").strip(), str(path))
                self.assertTrue(image.get("width", "").isdigit(), str(path))
                self.assertTrue(image.get("height", "").isdigit(), str(path))

    def test_navigation_has_keyboard_focus_and_touch_targets(self):
        css = (DIST / "assets/style.css").read_text(encoding="utf-8")
        self.assertIn("a:focus-visible{outline:", css)
        self.assertIn("min-height:44px;padding:8px 0", css)
        self.assertIn(".btn{min-height:48px", css)

    def test_gallery_images_keep_landscape_aspect_ratio(self):
        css = (DIST / "assets/style.css").read_text(encoding="utf-8")
        self.assertIn(".shot img{display:block;width:100%;height:auto;aspect-ratio:auto;", css)
        for lang in ("en", "ar"):
            parser = PageParser()
            parser.feed(output_path(lang).read_text(encoding="utf-8"))
            for image in parser.images[1:6]:
                self.assertEqual(image.get("width"), "526")
                self.assertEqual(image.get("height"), "296")

    def test_faq_has_measurable_google_play_cta(self):
        for lang in ("en", "ar"):
            parser = PageParser()
            parser.feed(output_path(lang, "faq").read_text(encoding="utf-8"))
            self.assertIn(APP["google_play_url"], parser.links)
            self.assertEqual([cta.get("data-cta-location") for cta in parser.tracked_ctas], ["faq_end"])

    def test_bilingual_blog_and_resource_pages_exist(self):
        for lang in ("en", "ar"):
            for tail in ("blog", "guide", "tips", "comparison"):
                self.assertTrue((DIST / lang / tail / "index.html").is_file())
            for article in DATA:
                path = DIST / lang / "blog" / article[0] / "index.html"
                self.assertTrue(path.is_file())
                source = path.read_text(encoding="utf-8")
                self.assertIn(article[1] if lang == "en" else article[2], source)
                self.assertIn('"@type": "Article"', source)
                self.assertIn('hreflang="ar"', source)
                self.assertIn('hreflang="en"', source)

    def test_guide_uses_all_five_real_store_screenshots(self):
        for lang in ("en", "ar"):
            parser = PageParser()
            parser.feed((DIST / lang / "guide" / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(len(parser.images), 5)
            self.assertTrue(all(image.get("alt") and image.get("width") == "526" for image in parser.images))
            manifest = json.loads((ROOT / "content/screenshots.json").read_text(encoding="utf-8"))
            self.assertEqual({i.get("src") for i in parser.images}, {s["src"] for s in manifest})

    def test_resource_navigation_is_present(self):
        for lang in ("en", "ar"):
            for tail in ("", "about", "features", "download", "faq", "blog", "guide", "tips", "comparison"):
                path = DIST / lang / tail / "index.html" if tail else DIST / lang / "index.html"
                source = path.read_text(encoding="utf-8")
                for section in ("blog", "guide", "tips", "comparison"):
                    self.assertIn(f'href="{BASE}/{lang}/{section}/"', source)

    def test_comparison_is_qualified_not_a_performance_benchmark(self):
        for lang in ("en", "ar"):
            source = (DIST / lang / "comparison" / "index.html").read_text(encoding="utf-8")
            self.assertIn("independent performance study" if lang == "en" else "مقارنة وصفية", source)

    def test_no_previous_brand(self):
        for path in DIST.rglob("*.html"):
            self.assertNotIn("Mingle", path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
