#!/usr/bin/env python3
import html
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP = json.loads((ROOT / "content/app.json").read_text(encoding="utf-8"))
FEATURES = json.loads((ROOT / "content/features.json").read_text(encoding="utf-8"))
FAQ = json.loads((ROOT / "content/faq.json").read_text(encoding="utf-8"))
BASE_URL = APP["website_url"].rstrip("/")

TEXT = {
    "en": {
        "about": "About Job Connect",
        "features": "Explore the features",
        "faq": "Frequently asked questions",
        "home": "Discover your next opportunity",
        "cta": "Open on Google Play",
        "tag": "JOB OPPORTUNITY DISCOVERY",
        "gallery": "A look inside the app",
        "download": "Get started with Job Connect",
        "privacy": "Privacy policy",
        "support": "Support",
        "about_intro": "Learn what Job Connect is designed to help you discover and organize.",
        "features_intro": "Explore the discovery and organization capabilities described for Job Connect.",
        "faq_intro": "Answers to common questions about Job Connect.",
        "language": "Choose your language",
        "english": "English",
        "arabic": "العربية",
        "home_intro": "Explore job opportunities, review useful context and keep track of roles that matter to you.",
    },
    "ar": {
        "about": "عن Job Connect",
        "features": "استكشف المزايا",
        "faq": "الأسئلة الشائعة",
        "home": "اكتشف فرصتك المهنية القادمة",
        "cta": "افتح التطبيق على Google Play",
        "tag": "اكتشاف فرص العمل",
        "gallery": "نظرة إلى واجهة التطبيق",
        "download": "ابدأ مع Job Connect",
        "privacy": "سياسة الخصوصية",
        "support": "الدعم",
        "about_intro": "تعرّف على Job Connect وما صُمم لمساعدتك على اكتشافه وتنظيمه.",
        "features_intro": "استكشف إمكانات الاكتشاف والتنظيم الموضحة لتطبيق Job Connect.",
        "faq_intro": "إجابات عن الأسئلة الشائعة حول Job Connect.",
        "language": "اختر لغتك",
        "english": "English",
        "arabic": "العربية",
        "home_intro": "استكشف فرص العمل وراجع سياقها المفيد واحتفظ بالوظائف التي تهمك للمتابعة.",
    },
}

PAGE_TITLES = {
    "en": {
        "home": "Job Connect — Discover job opportunities",
        "about": "About Job Connect",
        "features": "Job Connect features",
        "faq": "Job Connect — Frequently asked questions",
    },
    "ar": {
        "home": "Job Connect — اكتشف فرص العمل",
        "about": "عن Job Connect",
        "features": "مزايا Job Connect",
        "faq": "Job Connect — الأسئلة الشائعة",
    },
}

PAGE_DESCRIPTIONS = {
    "en": {
        "home": "Discover job opportunities with Job Connect. Explore roles, review opportunity context and organize roles worth following.",
        "about": "Learn about Job Connect, its purpose and the developer behind the Android application.",
        "features": "Explore Job Connect features for discovering job opportunities and organizing roles worth following.",
        "faq": "Find answers about Job Connect, its opportunity indicators, collections and official Android download.",
    },
    "ar": {
        "home": "اكتشف فرص العمل مع Job Connect. استكشف الوظائف وراجع تفاصيل الفرص ونظّم الوظائف التي تستحق المتابعة.",
        "about": "تعرّف على Job Connect وهدفه ومطور تطبيق Android.",
        "features": "استكشف مزايا Job Connect لاكتشاف فرص العمل وتنظيم الوظائف التي تستحق المتابعة.",
        "faq": "اعثر على إجابات حول Job Connect ومؤشرات الفرص والمجموعات وطريقة تنزيل التطبيق الرسمي.",
    },
}

CSS = """*{box-sizing:border-box}body{margin:0;background:#080b12;color:#f4f7fb;font:16px/1.75 system-ui,sans-serif}a{color:inherit}header,main,footer{width:min(1120px,calc(100% - 36px));margin:auto}header{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:22px 0;border-bottom:1px solid #263246}.brand{font-weight:900;text-decoration:none;letter-spacing:.08em}.brand b,.tag{color:#00c4df}nav{display:flex;gap:22px;flex-wrap:wrap}nav a{color:#c4ccda;text-decoration:none}.hero{padding:70px 0;display:grid;grid-template-columns:1fr .8fr;gap:44px;align-items:center}.tag{font-size:.8rem;letter-spacing:.16em;font-weight:700}.hero h1{font-size:clamp(2.5rem,6vw,4.6rem);line-height:1.12;margin:18px 0}.lead,.muted{color:#aab6c8}.btn{display:inline-block;background:#00c4df;color:#061018;text-decoration:none;padding:13px 20px;border-radius:9px;font-weight:800;margin-top:20px}.preview{padding:16px;background:#121a28;border:1px solid #29364b;border-radius:22px;text-align:center}.preview img{height:480px;max-width:100%;object-fit:contain;border-radius:12px}.section{padding:48px 0;border-top:1px solid #ffffff18}.section h2{font-size:2rem}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.item,.faq{background:#111925;border:1px solid #283449;border-radius:14px;padding:22px}.item h3,.faq h3{margin-top:0}.item p,.faq p{color:#aab6c8}.num{color:#00c4df;font:700 .8rem monospace}.faqgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.end{text-align:center;background:#11242d;border:1px solid #236071;border-radius:18px;padding:34px}.language{min-height:70vh;display:grid;place-items:center;text-align:center}.language a{display:inline-block;margin:8px;padding:14px 22px;border:1px solid #236071;border-radius:10px;text-decoration:none}footer{padding:30px 0;color:#aab6c8;border-top:1px solid #ffffff18;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}html[dir=rtl] body{text-align:right}html[dir=rtl] header{direction:rtl}@media(max-width:760px){.hero{grid-template-columns:1fr;padding:42px 0}.preview img{height:360px}.grid,.faqgrid{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column}nav{gap:14px}}"""

def esc(value):
    return html.escape(str(value), quote=True)

def page_url(lang, section="home"):
    suffix = "" if section == "home" else f"{section}/"
    return f"{BASE_URL}/{lang}/{suffix}"

def render_header(lang, section):
    t = TEXT[lang]
    nav_items = (("about", t["about"]), ("features", t["features"]), ("faq", t["faq"]))
    nav = "".join(
        f'<a href="{page_url(lang, key)}">{esc(label)}</a>'
        for key, label in nav_items
    )
    other = "ar" if lang == "en" else "en"
    switch_label = t["arabic"] if lang == "en" else t["english"]
    switch = f'<a lang="{other}" href="{page_url(other, section)}">{switch_label}</a>'
    return (
        f'<header><a class="brand" href="{BASE_URL}/">JOB <b>CONNECT</b></a>'
        f'<nav aria-label="Primary navigation">{nav}{switch}</nav></header>'
    )

def render_features(lang):
    cards = []
    for index, feature in enumerate(FEATURES, 1):
        cards.append(
            f'<article class="item"><div class="num">{index:02d} / FEATURE</div>'
            f'<h3>{esc(feature["title"][lang])}</h3>'
            f'<p>{esc(feature["description"][lang])}</p></article>'
        )
    return '<div class="grid">' + "".join(cards) + "</div>"

def render_faq(lang):
    cards = []
    for item in FAQ:
        cards.append(
            f'<article class="faq"><h3>{esc(item["q"][lang])}</h3>'
            f'<p>{esc(item["a"][lang])}</p></article>'
        )
    return '<div class="faqgrid">' + "".join(cards) + "</div>"

def render_content(lang, section):
    t = TEXT[lang]
    if section == "home":
        image = f'{BASE_URL}/assets/screens/screen-1.webp'
        return (
            f'<section class="hero"><div><div class="tag">{t["tag"]}</div>'
            f'<h1>{esc(t["home"])}</h1><p class="lead">{esc(t["home_intro"])}</p>'
            f'<a class="btn" href="{esc(APP["google_play_url"])}">{t["cta"]}</a></div>'
            f'<div class="preview"><img src="{image}" alt="{esc(t["gallery"])}"></div></section>'
            f'<section class="section"><h2>{t["features"]}</h2>{render_features(lang)}'
            f'<p><a href="{page_url(lang, "features")}">{t["features"]}</a></p></section>'
        )
    if section == "about":
        return (
            f'<section class="section"><div class="tag">JOB CONNECT</div>'
            f'<h1>{t["about"]}</h1><p class="lead">{esc(APP["description"][lang])}</p>'
            f'<p>{esc(t["about_intro"])}</p>'
            f'<p><strong>{esc(APP["developer"])}</strong></p>'
            f'<p><a class="btn" href="{esc(APP["google_play_url"])}">{t["cta"]}</a></p></section>'
        )
    if section == "features":
        return (
            f'<section class="section"><div class="tag">JOB CONNECT</div>'
            f'<h1>{t["features"]}</h1><p class="lead">{t["features_intro"]}</p>'
            f'{render_features(lang)}</section>'
        )
    if section == "faq":
        return (
            f'<section class="section"><div class="tag">JOB CONNECT</div>'
            f'<h1>{t["faq"]}</h1><p class="lead">{t["faq_intro"]}</p>'
            f'{render_faq(lang)}</section>'
        )
    raise ValueError(f"Unknown page section: {section}")

def render_page(lang, section):
    t = TEXT[lang]
    direction = "rtl" if lang == "ar" else "ltr"
    canonical = page_url(lang, section)
    description = PAGE_DESCRIPTIONS[lang][section]
    other = "ar" if lang == "en" else "en"
    schema = {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": APP["name"],
        "operatingSystem": "Android",
        "applicationCategory": "BusinessApplication",
        "description": APP["description"][lang],
        "downloadUrl": APP["google_play_url"],
        "url": canonical,
        "author": {"@type": "Organization", "name": APP["developer"]},
    }
    content = render_content(lang, section)
    return f'''<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(PAGE_TITLES[lang][section])}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{page_url("en", section)}">
<link rel="alternate" hreflang="ar" href="{page_url("ar", section)}">
<link rel="alternate" hreflang="x-default" href="{page_url("en", section)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(PAGE_TITLES[lang][section])}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="{BASE_URL}/assets/style.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>
{render_header(lang, section)}
<main>{content}</main>
<footer><span>© DevImpact · JOB CONNECT</span>
<span><a href="{esc(APP["privacy_policy_url"])}">{t["privacy"]}</a> ·
<a href="mailto:{esc(APP["support_email"])}">{t["support"]}</a></span></footer>
</body>
</html>'''

def render_language_root():
    canonical = f"{BASE_URL}/"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="8mOiNMu4Tn477yFaR-IWrNQGhdqH1TpF6NKKoN94Oms">
<title>Job Connect — Choose your language</title>
<meta name="description" content="Discover Job Connect, the Android job opportunity discovery app by DevImpact.">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{page_url("en")}">
<link rel="alternate" hreflang="ar" href="{page_url("ar")}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<link rel="stylesheet" href="{BASE_URL}/assets/style.css">
</head>
<body><main class="language"><div><div class="tag">JOB CONNECT</div>
<h1>Choose your language / اختر لغتك</h1>
<p><a lang="en" href="{page_url("en")}">English</a>
<a lang="ar" dir="rtl" href="{page_url("ar")}">العربية</a></p></div></main></body>
</html>'''

def write(relative_path, content):
    target = DIST / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    write(pathlib.Path("assets/style.css"), CSS)
    shutil.copytree(ROOT / "assets/screens", DIST / "assets/screens")
    write(pathlib.Path("index.html"), render_language_root())
    for lang in ("en", "ar"):
        for section in ("home", "about", "features", "faq"):
            relative = pathlib.Path(lang) / ("" if section == "home" else section) / "index.html"
            write(relative, render_page(lang, section))
    write(pathlib.Path("robots.txt"), f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    sitemap_urls = [f"{BASE_URL}/"]
    sitemap_urls.extend(page_url(lang, section) for lang in ("en", "ar") for section in ("home", "about", "features", "faq"))
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    sitemap += "".join(f"<url><loc>{esc(url)}</loc></url>" for url in sitemap_urls)
    sitemap += "</urlset>"
    write(pathlib.Path("sitemap.xml"), sitemap)
    write(pathlib.Path("llms.txt"), (
        f"# Job Connect\n\n{APP['description']['en']}\n\n"
        f"- Google Play: {APP['google_play_url']}\n"
        f"- English: {page_url('en')}\n- Arabic: {page_url('ar')}\n"
    ))

if __name__ == "__main__":
    main()
