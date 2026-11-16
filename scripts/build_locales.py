#!/usr/bin/env python3
"""Generate only fully translated, explicitly published market locales."""
import html
import json
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
STRATEGY = json.loads((ROOT / "content/market-strategy.json").read_text(encoding="utf-8"))
LOCALES = json.loads((ROOT / "content/locales.json").read_text(encoding="utf-8"))
BASE = APP["website_url"].rstrip("/")
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML = "http://www.w3.org/1999/xhtml"
SECTIONS = ("home", "about", "features", "download", "faq")

def slug(locale):
    return locale.lower()

def locale_parts(locale):
    language, region = locale.split("-", 1)
    return language, region

def replace_text(source, old, new):
    if old and old != new:
        source = source.replace(html.escape(old, quote=False), html.escape(new, quote=True))
    return source

def localize(source, locale, section, route_tail=None):
    import build
    language, region = locale_parts(locale)
    data = LOCALES.get(locale, {})
    replacements = []
    for key, value in build.TEXT["en"].items():
        if key in data.get("text", {}):
            replacements.append((value, data["text"][key]))
    for key, value in build.PAGE_TITLES["en"].items():
        if key in data.get("titles", {}):
            replacements.append((value, data["titles"][key]))
    for key, value in build.PAGE_DESCRIPTIONS["en"].items():
        if key in data.get("descriptions", {}):
            replacements.append((value, data["descriptions"][key]))
    if data.get("app_description"):
        replacements.append((APP["description"]["en"], data["app_description"]))
    if data.get("tagline"):
        replacements.append((APP["tagline"]["en"], data["tagline"]))
    replacements.extend([
        ("Explore this feature", "Explorer cette fonctionnalité")
        for _ in [0] if language == "fr"
    ])
    if data.get("features"):
        for feature, translated in zip(build.FEATURES, data["features"]):
            replacements.extend([(feature["title"]["en"], translated[0]),
                                 (feature["description"]["en"], translated[1])])
    if data.get("faq"):
        for item, translated in zip(build.FAQ, data["faq"]):
            replacements.extend([(item["q"]["en"], translated[0]),
                                 (item["a"]["en"], translated[1])])
    if data.get("screenshots"):
        for screenshot, translated in zip(build.SCREENSHOTS, data["screenshots"]):
            replacements.extend([(screenshot["alt"]["en"], translated[0]),
                                 (screenshot["caption"]["en"], translated[1])])
    for old, new in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
        source = replace_text(source, old, new)
    if locale == "fr-CA":
        source = source.replace('og:locale" content="en_US"', 'og:locale" content="fr_CA"')
    elif locale == "en-CA":
        source = source.replace('og:locale" content="en_US"', 'og:locale" content="en_CA"')
        source = source.replace("Job listings", "Job postings").replace("job listings", "job postings")
        source = source.replace("Job listing", "Job posting").replace("job listing", "job posting")
    # Convert every internal English route, including navigation and feature anchors.
    source = source.replace(f"{BASE}/en/", f"{BASE}/{slug(locale)}/")
    source = source.replace('<html lang="en"', f'<html lang="{locale}"')
    # The legacy bilingual switch is replaced with an explicit three-market selector.
    source = re.sub(
        r'<a lang="ar" href="[^"]+">العربية</a>',
        '<span class="locale-switch"><a lang="en-US" href="' + BASE + '/en-us/' + '">US English</a> · '
        '<a lang="en-CA" href="' + BASE + '/en-ca/' + '">English (Canada)</a> · '
        '<a lang="fr-CA" href="' + BASE + '/fr-ca/' + '">Français (Canada)</a></span>',
        source,
    )
    source = re.sub(
        r'<link rel="alternate" hreflang="(?:en|ar|x-default)" href="[^"]+">\n?',
        "",
        source,
    )
    tail = route_tail if route_tail is not None else ("" if section == "home" else f"{section}/")
    canonical = f"{BASE}/{slug(locale)}/{tail}"
    alternates = (
        f'<link rel="alternate" hreflang="en-US" href="{BASE}/en-us/{tail}">\\n'
        f'<link rel="alternate" hreflang="en-CA" href="{BASE}/en-ca/{tail}">\\n'
        f'<link rel="alternate" hreflang="fr-CA" href="{BASE}/fr-ca/{tail}">\\n'
        f'<link rel="alternate" hreflang="x-default" href="{BASE}/en-us/{tail}">'
    )
    source = source.replace(f'<link rel="canonical" href="{canonical}">', 
                            f'<link rel="canonical" href="{canonical}">\\n{alternates}')
    return source

def build_localized_pages():
    published = STRATEGY.get("published_locales", [])
    if not published:
        raise ValueError("market-strategy.json must explicitly list published_locales")
    market_locales = {
        locale
        for market in STRATEGY["markets"]
        if market.get("status") == "initial"
        for locale in market.get("locales", [])
    }
    if not set(published).issubset(market_locales):
        raise ValueError("A published locale must belong to an initial market")
    if set(published) != set(LOCALES.keys()) | {"en-US", "en-CA"}:
        raise ValueError("Every published locale must have complete locale content")
    for locale in published:
        if locale not in ("en-US", "en-CA") and locale not in LOCALES:
            raise ValueError(f"Missing translation bundle for {locale}")
        for section in SECTIONS:
            source_path = DIST / "en" / ("" if section == "home" else section) / "index.html"
            source = source_path.read_text(encoding="utf-8")
            write_path = DIST / slug(locale) / ("" if section == "home" else section) / "index.html"
            write_path.parent.mkdir(parents=True, exist_ok=True)
            write_path.write_text(localize(source, locale, section), encoding="utf-8")
    import build
    for locale in published:
        for feature in build.FEATURES:
            tail = f"features/{feature['id']}/"
            source_path = DIST / "en" / "features" / feature["id"] / "index.html"
            source = source_path.read_text(encoding="utf-8")
            target = DIST / slug(locale) / tail / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(localize(source, locale, "features", tail), encoding="utf-8")
    update_root_page(published)
    update_sitemaps(published)
    llms = DIST / "llms.txt"
    existing = llms.read_text(encoding="utf-8")
    existing += "\n## Published market locales\n"
    for locale in published:
        existing += f"- {locale}: {BASE}/{slug(locale)}/\n"
    llms.write_text(existing, encoding="utf-8")

def update_root_page(published):
    path = DIST / "index.html"
    source = path.read_text(encoding="utf-8")
    source = re.sub(r'<link rel="alternate" hreflang="(?:en|ar|x-default)" href="[^"]+">\n?', "", source)
    links = "".join(
        f'<link rel="alternate" hreflang="{locale}" href="{BASE}/{slug(locale)}/">\n'
        for locale in published
    )
    links += f'<link rel="alternate" hreflang="x-default" href="{BASE}/">'
    source = source.replace(f'<link rel="canonical" href="{BASE}/">', 
                            f'<link rel="canonical" href="{BASE}/">\n{links}')
    source = re.sub(r'<p><a lang="en" href="[^"]+">English</a>\s*<a lang="ar" dir="rtl" href="[^"]+">العربية</a></p>',
        f'<p><a lang="en-US" href="{BASE}/en-us/">US English</a> · '
        f'<a lang="en-CA" href="{BASE}/en-ca/">English (Canada)</a> · '
        f'<a lang="fr-CA" href="{BASE}/fr-ca/">Français (Canada)</a></p>', source)
    path.write_text(source, encoding="utf-8")

def update_sitemaps(published):
    xml_path = DIST / "sitemap.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ET.register_namespace("", NS)
    ET.register_namespace("xhtml", XHTML)
    root_entry = next((node for node in root.findall(f"{{{NS}}}url")
                       if node.findtext(f"{{{NS}}}loc") == f"{BASE}/"), None)
    if root_entry is not None:
        for item in list(root_entry):
            if item.tag == f"{{{XHTML}}}link":
                root_entry.remove(item)
        for locale in published:
            ET.SubElement(root_entry, f"{{{XHTML}}}link", {
                "rel": "alternate", "hreflang": locale, "href": f"{BASE}/{slug(locale)}/"
            })
        ET.SubElement(root_entry, f"{{{XHTML}}}link", {
            "rel": "alternate", "hreflang": "x-default", "href": f"{BASE}/"
        })
    for section in SECTIONS:
        path_tail = "" if section == "home" else f"{section}/"
        alternates = [(locale, f"{BASE}/{slug(locale)}/{path_tail}") for locale in published]
        for locale, url in alternates:
            node = ET.SubElement(root, f"{{{NS}}}url")
            ET.SubElement(node, f"{{{NS}}}loc").text = url
            for alt_locale, alt_url in alternates:
                ET.SubElement(node, f"{{{XHTML}}}link", {
                    "rel": "alternate", "hreflang": alt_locale, "href": alt_url
                })
            ET.SubElement(node, f"{{{XHTML}}}link", {
                "rel": "alternate", "hreflang": "x-default", "href": alternates[0][1]
            })
    import build
    for feature in build.FEATURES:
        tail = f"features/{feature['id']}/"
        alternates = [(locale, f"{BASE}/{slug(locale)}/{tail}") for locale in published]
        for locale, url in alternates:
            node = ET.SubElement(root, f"{{{NS}}}url")
            ET.SubElement(node, f"{{{NS}}}loc").text = url
            for alt_locale, alt_url in alternates:
                ET.SubElement(node, f"{{{XHTML}}}link", {
                    "rel": "alternate", "hreflang": alt_locale, "href": alt_url
                })
            ET.SubElement(node, f"{{{XHTML}}}link", {
                "rel": "alternate", "hreflang": "x-default", "href": alternates[0][1]
            })
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    urls = [line.strip() for line in (DIST / "sitemap.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    for section in SECTIONS:
        tail = "" if section == "home" else f"{section}/"
        urls.extend(f"{BASE}/{slug(locale)}/{tail}" for locale in published)
    for feature in build.FEATURES:
        tail = f"features/{feature['id']}/"
        urls.extend(f"{BASE}/{slug(locale)}/{tail}" for locale in published)
    (DIST / "sitemap.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")

def main():
    build_localized_pages()

if __name__ == "__main__":
    main()
