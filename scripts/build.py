#!/usr/bin/env python3
"""Build a bilingual, static and crawler-readable Job Connect discovery site."""
import html, json, pathlib, shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"dist"
APP=json.loads((ROOT/"content/app.json").read_text(encoding="utf-8"))
FEATURES=json.loads((ROOT/"content/features.json").read_text(encoding="utf-8"))
FAQ=json.loads((ROOT/"content/faq.json").read_text(encoding="utf-8"))
BASE=APP["website_url"].rstrip("/")
TEXT={
 "en":{"tag":"Find your next opportunity","about":"About","features":"Features","faq":"FAQ","install":"Get it on Google Play","about_title":"About Job Connect","features_title":"Explore Job Connect features","faq_title":"Frequently asked questions","privacy":"Privacy policy","support":"Contact support","description":"Discover job opportunities with Job Connect. Search listings, set job alerts and save jobs."},
 "ar":{"tag":"اكتشف فرصتك المهنية القادمة","about":"عن التطبيق","features":"المزايا","faq":"الأسئلة الشائعة","install":"احصل عليه من Google Play","about_title":"عن Job Connect","features_title":"اكتشف مزايا Job Connect","faq_title":"الأسئلة الشائعة","privacy":"سياسة الخصوصية","support":"التواصل مع الدعم","description":"اكتشف فرص العمل مع Job Connect. ابحث عن الوظائف وأعدّ التنبيهات واحفظ الوظائف."}
}
CSS="""*{box-sizing:border-box}body{margin:0;font:16px/1.75 system-ui,-apple-system,Segoe UI,sans-serif;color:#172033;background:#f7f9fc}a{color:#1456b8}header,main,footer{max-width:980px;margin:auto;padding:22px}header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}.brand{font-weight:800;font-size:1.25rem;text-decoration:none;color:#172033}nav{display:flex;gap:16px;flex-wrap:wrap}main{padding-top:44px;padding-bottom:64px}.hero,.panel,article{background:white;border:1px solid #e5eaf2;border-radius:18px;padding:24px;margin:18px 0}.hero h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.15;margin:.2em 0}.muted{color:#596579}.cta{display:inline-block;background:#1456b8;color:white;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.lang{white-space:nowrap}footer{border-top:1px solid #e5eaf2;color:#596579}html[dir=rtl] body{text-align:right}html[dir=rtl] header{direction:rtl}"""
def e(v): return html.escape(str(v),quote=True)
def page(lang,section):
 t=TEXT[lang]; rtl=lang=="ar"; title={"home":APP["name"],"about":t["about_title"],"features":t["features_title"],"faq":t["faq_title"]}[section]
 path="" if section=="home" else section
 canonical=f"{BASE}/{lang}/"+(f"{path}/" if path else "")
 prefix="../" if path else ""
 nav="".join(f'<a href="{prefix}{p}/">{e(t[k])}</a>' for p,k in [("about","about"),("features","features"),("faq","faq")])
 switch=f'<a class="lang" href="{BASE}/{"en" if rtl else "ar"}/{path + "/" if path else ""}">{"English" if rtl else "العربية"}</a>'
 css_path=("../../" if path else "../")+"assets/style.css"
 ld={"@context":"https://schema.org","@type":"MobileApplication","name":APP["name"],"operatingSystem":"Android","applicationCategory":"BusinessApplication","description":APP["description"][lang],"downloadUrl":APP["google_play_url"],"installUrl":APP["google_play_url"],"url":canonical,"author":{"@type":"Organization","name":APP["developer"]}}
 body=""
 if section in ("home","about"):
  body=f'<section class="hero"><p class="muted">{e(t["tag"])}</p><h1>{e(APP["name"])}</h1><p>{e(APP["description"][lang])}</p><p><a class="cta" href="{e(APP["google_play_url"])}" rel="nofollow">{e(t["install"])}</a></p></section>'
  if section=="about": body+=f'<section class="panel"><h2>{e(t["about_title"])}</h2><p>{e(t["description"])}</p><p>{e(APP["developer"])} · Android · {e(APP["category"])}</p></section>'
 elif section=="features":
  cards="".join(f'<article><h2>{e(x["title"][lang])}</h2><p>{e(x["description"][lang])}</p></article>' for x in FEATURES)
  body=f'<h1>{e(t["features_title"])}</h1><div class="grid">{cards}</div>'
 else:
  items="".join(f'<article><h2>{e(x["q"][lang])}</h2><p>{e(x["a"][lang])}</p></article>' for x in FAQ)
  body=f'<h1>{e(t["faq_title"])}</h1>{items}'
 return f'''<!doctype html><html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | Job Connect</title><meta name="description" content="{e(t["description"])}"><link rel="canonical" href="{e(canonical)}"><link rel="alternate" hreflang="en" href="{BASE}/en/{path + '/' if path else ''}"><link rel="alternate" hreflang="ar" href="{BASE}/ar/{path + '/' if path else ''}"><link rel="alternate" hreflang="x-default" href="{BASE}/en/{path + '/' if path else ''}"><meta property="og:type" content="website"><meta property="og:title" content="{e(title)} | Job Connect"><meta property="og:description" content="{e(t["description"])}"><meta property="og:url" content="{e(canonical)}"><meta name="theme-color" content="#1456b8"><link rel="stylesheet" href="{css_path}"><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script></head><body><header><a class="brand" href="{prefix}">Job Connect</a><nav>{nav}{switch}</nav></header><main>{body}</main><footer><p>{e(APP["developer"])} · <a href="{e(APP["privacy_policy_url"])}">{e(t["privacy"])}</a> · <a href="mailto:{e(APP["support_email"])}">{e(t["support"])}</a></p></footer></body></html>'''
def write(path,data):
 target=OUT/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(data,encoding="utf-8")
def main():
 if OUT.exists(): shutil.rmtree(OUT)
 write(pathlib.Path("assets/style.css"),CSS)
 for lang in ("en","ar"):
  for section in ("home","about","features","faq"):
   folder=pathlib.Path(lang) if section=="home" else pathlib.Path(lang)/section
   write(folder/"index.html",page(lang,section))
 write(pathlib.Path("index.html"),'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=./en/"><link rel="canonical" href="'+BASE+'/en/"><title>Job Connect</title></head><body><p><a href="./en/">English</a> · <a href="./ar/">العربية</a></p></body></html>')
 write(pathlib.Path("robots.txt"),"User-agent: *\nAllow: /\nSitemap: "+BASE+"/sitemap.xml\n")
 urls=[f"{BASE}/{l}/{s + '/' if s else ''}" for l in ("en","ar") for s in ("","about","features","faq")]
 write(pathlib.Path("sitemap.xml"),'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(u)+'</loc></url>' for u in urls)+'</urlset>')
 write(pathlib.Path("llms.txt"),f"# Job Connect\n\n{APP['description']['en']}\n\n- Google Play: {APP['google_play_url']}\n- English: {BASE}/en/\n- العربية: {BASE}/ar/\n- Features: {BASE}/en/features/\n- FAQ: {BASE}/en/faq/\n")
if __name__=="__main__": main()
