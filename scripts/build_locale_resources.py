#!/usr/bin/env python3
"""Generate the four career-resource hub routes for every published market locale."""
import html
import json
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
STRATEGY = json.loads((ROOT / "content/market-strategy.json").read_text(encoding="utf-8"))
BASE = APP["website_url"].rstrip("/")
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML = "http://www.w3.org/1999/xhtml"
HUBS = ("tips", "blog", "guide", "comparison")
EXTRA_CONTENT = json.loads((ROOT / "content/resource-locales.json").read_text(encoding="utf-8"))

CONTENT = {
    "en-US": {
        "language_name": "US English",
        "nav": {"tips": "Tips", "blog": "Blog", "guide": "User guide", "comparison": "Compare"},
        "pages": {
            "tips": ("Job Search Tips | Job Connect", "Practical job-search tips for reviewing opportunities, checking listings and organizing your next steps.", "Job search tips", "Build a focused search, verify the original listing and use app indicators as context—not guarantees.", [
                ("Set a focused search", "Choose relevant roles and priorities so you can assess opportunities consistently.", "guide"),
                ("Verify every listing", "Check the employer, requirements, location and application instructions at the original source.", "blog"),
                ("Use indicators carefully", "Treat freshness, match and competition signals as supporting information, not promises.", "comparison")]),
            "blog": ("Job Search Blog & Career Resources | Job Connect", "Career resources from Job Connect: practical tips, a user guide and a clear workflow comparison.", "Job Connect career resources", "Explore practical resources to make your job search more organized, informed and careful.", [
                ("Job search tips", "Practical habits for evaluating opportunities and protecting your time and information.", "tips"),
                ("User guide", "A concise walkthrough of discovering, reviewing and organizing opportunities with Job Connect.", "guide"),
                ("Compare workflows", "Understand how an opportunity-discovery app fits alongside traditional job-search methods.", "comparison")]),
            "guide": ("Job Connect User Guide | Job Search App", "Learn how to explore opportunities, review role context and organize jobs with Job Connect.", "Job Connect user guide", "Follow a simple workflow for discovering opportunities, reviewing details and keeping track of roles.", [
                ("Discover opportunities", "Explore the discovery experience and decide which roles deserve a closer look.", "tips"),
                ("Review role details", "Read responsibilities and requirements, and verify important details with the employer.", "blog"),
                ("Organize your search", "Use personal collections to group opportunities you want to revisit.", "comparison")]),
            "comparison": ("Job Search Workflow Comparison | Job Connect", "A qualitative comparison of app-based opportunity discovery and traditional job-search routines.", "Compare job-search workflows", "See where an opportunity-discovery app can help—and what still requires independent verification.", [
                ("Finding opportunities", "A dedicated discovery view can reduce the need to revisit scattered sources manually.", "guide"),
                ("Reviewing context", "App indicators add context, while the original employer listing remains the source to verify.", "tips"),
                ("Organizing roles", "Personal collections can keep opportunities together for later review and follow-up.", "blog")])
        }
    },
    "en-CA": {
        "language_name": "English (Canada)",
        "nav": {"tips": "Tips", "blog": "Blog", "guide": "User guide", "comparison": "Compare"},
        "pages": {
            "tips": ("Job Search Tips | Job Connect", "Practical job-search tips for reviewing opportunities, checking job postings and organizing next steps.", "Job search tips", "Build a focused search, verify the original job posting and use app indicators as context—not guarantees.", [
                ("Set a focused search", "Choose relevant roles and priorities so you can assess opportunities consistently.", "guide"),
                ("Verify every posting", "Check the employer, requirements, location and application instructions at the original source.", "blog"),
                ("Use indicators carefully", "Treat freshness, match and competition signals as supporting information, not promises.", "comparison")]),
            "blog": ("Job Search Blog & Career Resources | Job Connect", "Career resources from Job Connect: practical tips, a user guide and a clear workflow comparison.", "Job Connect career resources", "Explore practical resources to make your job search more organized, informed and careful.", [
                ("Job search tips", "Practical habits for evaluating opportunities and protecting your time and information.", "tips"),
                ("User guide", "A concise walkthrough of discovering, reviewing and organizing opportunities with Job Connect.", "guide"),
                ("Compare workflows", "Understand how an opportunity-discovery app fits alongside traditional job-search methods.", "comparison")]),
            "guide": ("Job Connect User Guide | Job Search App", "Learn how to explore opportunities, review role context and organize jobs with Job Connect.", "Job Connect user guide", "Follow a simple workflow for discovering opportunities, reviewing details and keeping track of roles.", [
                ("Discover opportunities", "Explore the discovery experience and decide which roles deserve a closer look.", "tips"),
                ("Review job details", "Read responsibilities and requirements, and verify important details with the employer.", "blog"),
                ("Organize your search", "Use personal collections to group opportunities you want to revisit.", "comparison")]),
            "comparison": ("Job Search Workflow Comparison | Job Connect", "A qualitative comparison of app-based opportunity discovery and traditional job-search routines.", "Compare job-search workflows", "See where an opportunity-discovery app can help—and what still requires independent verification.", [
                ("Finding opportunities", "A dedicated discovery view can reduce the need to revisit scattered sources manually.", "guide"),
                ("Reviewing context", "App indicators add context, while the original employer posting remains the source to verify.", "tips"),
                ("Organizing roles", "Personal collections can keep opportunities together for later review and follow-up.", "blog")])
        }
    },
    "fr-CA": {
        "language_name": "Français (Canada)",
        "nav": {"tips": "Conseils", "blog": "Blogue", "guide": "Guide", "comparison": "Comparer"},
        "pages": {
            "tips": ("Conseils pour la recherche d’emploi | Job Connect", "Des conseils pratiques pour examiner les possibilités, vérifier les offres et organiser vos prochaines étapes.", "Conseils pour la recherche d’emploi", "Définissez une recherche ciblée, vérifiez l’offre originale et utilisez les indicateurs comme contexte, jamais comme garantie.", [
                ("Ciblez votre recherche", "Choisissez les postes et les priorités qui correspondent à vos objectifs pour évaluer les possibilités avec méthode.", "guide"),
                ("Vérifiez chaque offre", "Consultez la source originale pour confirmer l’employeur, les exigences, le lieu et les modalités de candidature.", "blog"),
                ("Interprétez les indicateurs avec prudence", "La fraîcheur, la correspondance et la concurrence sont des indices utiles, pas des promesses.", "comparison")]),
            "blog": ("Blogue et ressources carrière | Job Connect", "Des ressources Job Connect : conseils pratiques, guide d’utilisation et comparaison des méthodes de recherche.", "Ressources carrière Job Connect", "Consultez des ressources pratiques pour organiser votre recherche d’emploi et examiner les possibilités avec discernement.", [
                ("Conseils de recherche d’emploi", "Des habitudes utiles pour évaluer les possibilités et protéger votre temps et vos renseignements.", "tips"),
                ("Guide d’utilisation", "Un parcours simple pour découvrir, examiner et organiser les possibilités avec Job Connect.", "guide"),
                ("Comparer les méthodes", "Comprenez comment une application de découverte complète les méthodes traditionnelles de recherche.", "comparison")]),
            "guide": ("Guide d’utilisation de Job Connect | Android", "Apprenez à découvrir des possibilités, à examiner leur contexte et à organiser les postes avec Job Connect.", "Guide d’utilisation de Job Connect", "Suivez un parcours simple pour découvrir des possibilités, examiner les détails et retrouver les postes à suivre.", [
                ("Découvrir des possibilités", "Explorez l’écran de découverte et repérez les postes qui méritent un examen plus approfondi.", "tips"),
                ("Examiner les détails", "Lisez les responsabilités et les exigences, puis vérifiez les renseignements importants auprès de l’employeur.", "blog"),
                ("Organiser votre recherche", "Utilisez les collections personnelles pour regrouper les possibilités à consulter de nouveau.", "comparison")]),
            "comparison": ("Comparer les méthodes de recherche d’emploi | Job Connect", "Une comparaison qualitative entre la découverte dans une application et les méthodes traditionnelles de recherche d’emploi.", "Comparer les méthodes de recherche d’emploi", "Découvrez comment une application de découverte peut vous aider et quelles informations doivent toujours être vérifiées.", [
                ("Repérer des possibilités", "Un fil de découverte dédié peut réduire les recherches manuelles sur plusieurs sources.", "guide"),
                ("Examiner le contexte", "Les indicateurs ajoutent du contexte, mais l’offre originale de l’employeur reste la source à vérifier.", "tips"),
                ("Organiser les postes", "Les collections personnelles regroupent les possibilités à consulter et à suivre plus tard.", "blog")])
        }
    }
}
CONTENT.update(EXTRA_CONTENT)

FLAG_DATA = {
    "en-US": ("us", "United States", "United States · English"),
    "en-CA": ("ca", "Canada", "Canada · English"),
    "fr-CA": ("ca", "Canada", "Canada · Français"),
    "es-ES": ("es", "Spain", "España · Español"),
    "pt-PT": ("pt", "Portugal", "Portugal · Português"),
    "fr-FR": ("fr", "France", "France · Français"),
    "de-DE": ("de", "Germany", "Deutschland · Deutsch"),
    "it-IT": ("it", "Italy", "Italia · Italiano"),
}
NAV_GROUPS = {
    "en-US": ("Explore", "Resources"), "en-CA": ("Explore", "Resources"),
    "fr-CA": ("Explorer", "Ressources"), "es-ES": ("Explorar", "Recursos"),
    "pt-PT": ("Explorar", "Recursos"), "fr-FR": ("Explorer", "Ressources"),
    "de-DE": ("Entdecken", "Ressourcen"), "it-IT": ("Esplora", "Risorse"),
}
LOCALE_TEXT = json.loads((ROOT / "content/locales.json").read_text(encoding="utf-8"))

def render_locale_flags(locale, tail):
    links = []
    for code in STRATEGY["published_locales"]:
        country, country_name, label = FLAG_DATA[code]
        current = ' aria-current="page"' if code == locale else ""
        flag_url = f"https://flagcdn.com/w80/{country}.png"
        links.append(
            f'<a class="locale-flag" lang="{code}" href="{route(code, tail)}" '
            f'title="{esc(label)}" aria-label="{esc(label)}"{current}>'
            f'<img src="{flag_url}" alt="{esc(country_name)} flag" width="40" height="30" loading="eager" decoding="async"></a>'
        )
    import build
    return '<div class="locale-switch" aria-label="Country and region">' + "".join(links) + build.render_social_links() + '</div>'

def esc(value):
    return html.escape(str(value), quote=True)

def route(locale, tail):
    return f"{BASE}/{locale.lower()}/{tail}/"

def render_page(locale, tail, data):
    language = locale.split("-", 1)[0]
    labels = CONTENT[locale].get("labels", {
        "features": "Fonctionnalités" if language == "fr" else "Features",
        "more": "En savoir plus" if language == "fr" else "Explore this resource",
        "skip": "Passer au contenu principal" if language == "fr" else "Skip to main content",
        "resource": "RESSOURCES CARRIÈRE" if language == "fr" else "CAREER RESOURCES",
        "home": "Retour à l’accueil" if language == "fr" else "Back to the home page",
        "privacy": "Politique de confidentialité" if language == "fr" else "Privacy policy",
        "support": "Soutien" if language == "fr" else "Support",
        "nav_aria": "Navigation principale" if language == "fr" else "Primary navigation"
    })
    title, description, heading, intro, cards = data
    slug = locale.lower()
    alternates = "".join(
        f'<link rel="alternate" hreflang="{code}" href="{route(code, tail)}">\n'
        for code in STRATEGY["published_locales"]
    )
    alternates += f'<link rel="alternate" hreflang="x-default" href="{route("en-US", tail)}">'
    nav_groups = NAV_GROUPS[locale]
    primary_text = LOCALE_TEXT.get(locale, {}).get("text", {})
    primary_items = (
        ("about", primary_text.get("about", "About")),
        ("features", primary_text.get("features", labels["features"])),
        ("download", primary_text.get("download_nav", "Download")),
        ("faq", primary_text.get("faq", "FAQ")),
    )
    primary_links = "".join(
        f'<a data-nav-item="{key}" href="{BASE}/{slug}/{key}/">{esc(label)}</a>'
        for key, label in primary_items
    )
    resource_links = "".join(
        f'<a data-nav-item="{item}" href="{route(locale, item)}">{esc(CONTENT[locale]["nav"][item])}</a>'
        for item in ("tips", "blog", "guide", "comparison")
    )
    nav = (
        f'<details class="nav-menu" data-nav-group="primary"><summary>{esc(nav_groups[0])}</summary>'
        f'<div class="nav-dropdown">{primary_links}</div></details>'
        f'<details class="nav-menu" data-nav-group="resources"><summary>{esc(nav_groups[1])}</summary>'
        f'<div class="nav-dropdown">{resource_links}</div></details>'
    )
    cards_html = "".join(
        f'<article class="item"><h2><a href="{route(locale, target)}">{esc(card_title)}</a></h2>'
        f'<p>{esc(card_text)}</p><a href="{route(locale, target)}">'
        f'{esc(labels["more"])}</a></article>'
        for card_title, card_text, target in cards
    )
    locale_links = " · ".join(
        f'<a lang="{code}" href="{route(code, tail)}">{esc(CONTENT[code]["language_name"])}</a>'
        for code in STRATEGY["published_locales"] if code != locale
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "inLanguage": locale,
        "url": route(locale, tail),
        "publisher": {"@type": "Organization", "name": APP["developer"], "url": BASE + "/"}
    }
    return f'''<!doctype html>
<html lang="{esc(locale)}" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{route(locale, tail)}">
{alternates}
<meta property="og:type" content="website">
<meta property="og:locale" content="{"fr_CA" if locale == "fr-CA" else locale.replace("-", "_")}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{route(locale, tail)}">
<link rel="stylesheet" href="{BASE}/assets/style.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body data-page-section="{tail}">
<a class="skip-link" href="#main-content">{esc(labels["skip"])}</a>
<header class="standard-header"><div class="header-main">{render_locale_flags(locale, tail)}<a class="brand" href="{BASE}/{slug}/">JOB <b>CONNECT</b></a>
<nav aria-label="{esc(labels["nav_aria"])}">{nav}</nav></div></header>
<main id="main-content"><section class="section resource-hub">
<div class="tag">JOB CONNECT · {esc(labels["resource"])}</div>
<h1>{esc(heading)}</h1><p class="lead">{esc(intro)}</p>
<div class="grid">{cards_html}</div>
<p class="locale-links">{locale_links}</p>
<p><a href="{BASE}/{slug}/">{esc(labels["home"])}</a></p>
</section></main>
<footer><span>© DevImpact · JOB CONNECT</span><span><a href="{esc(APP["privacy_policy_url"])}">{esc(labels["privacy"])}</a> · <a href="mailto:{esc(APP["support_email"])}">{esc(labels["support"])}</a></span></footer>
</body>
</html>'''

def build_localized_resource_pages():
    published = STRATEGY.get("published_locales", [])
    if set(published) != set(CONTENT):
        raise ValueError("Localized resource content must exist for every published locale")
    css = DIST / "assets/style.css"
    css.write_text(
        css.read_text(encoding="utf-8")
        + "\n.resource-hub{max-width:1000px}.resource-hub h1{font-size:clamp(2.2rem,5vw,3.6rem);line-height:1.15}.resource-hub .grid{margin-top:28px}.resource-hub .item h2{font-size:1.3rem}.locale-links{margin-top:30px;color:#aab6c8}\n",
        encoding="utf-8"
    )
    for locale in published:
        for tail in HUBS:
            target = DIST / locale.lower() / tail / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_page(locale, tail, CONTENT[locale]["pages"][tail]), encoding="utf-8")

    sitemap_path = DIST / "sitemap.xml"
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ET.register_namespace("", NS)
    ET.register_namespace("xhtml", XHTML)
    existing = {
        node.findtext(f"{{{NS}}}loc")
        for node in root.findall(f"{{{NS}}}url")
    }
    for locale in published:
        for tail in HUBS:
            loc = route(locale, tail)
            if loc in existing:
                continue
            node = ET.SubElement(root, f"{{{NS}}}url")
            ET.SubElement(node, f"{{{NS}}}loc").text = loc
            for alternate_locale in published:
                ET.SubElement(node, f"{{{XHTML}}}link", {
                    "rel": "alternate", "hreflang": alternate_locale,
                    "href": route(alternate_locale, tail)
                })
            ET.SubElement(node, f"{{{XHTML}}}link", {
                "rel": "alternate", "hreflang": "x-default",
                "href": route("en-US", tail)
            })
    tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)

    text_path = DIST / "sitemap.txt"
    urls = [line.strip() for line in text_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for locale in published:
        for tail in HUBS:
            loc = route(locale, tail)
            if loc not in urls:
                urls.append(loc)
    text_path.write_text("\n".join(urls) + "\n", encoding="utf-8")

    llms_path = DIST / "llms.txt"
    llms = llms_path.read_text(encoding="utf-8")
    llms += "\n## Localized career resources\n"
    for locale in published:
        for tail in HUBS:
            llms += f"- {locale} {tail}: {route(locale, tail)}\n"
    llms_path.write_text(llms, encoding="utf-8")

if __name__ == "__main__":
    build_localized_resource_pages()
