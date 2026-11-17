#!/usr/bin/env python3
import json,pathlib,re,sys,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]; DIST=ROOT/"dist"; APP=json.loads((ROOT/"content/app.json").read_text()); STR=json.loads((ROOT/"content/market-strategy.json").read_text()); BASE=APP["website_url"].rstrip("/"); errors=[]
for p in DIST.rglob("*.html"):
 s=p.read_text()
 if p==DIST/"index.html" or p.parent.parent==DIST: continue
 if "Job Connect" in s or "job search" in s.lower() or "job posting" in s.lower(): errors.append("Legacy job content: "+str(p))
 if '<meta name="description"' not in s or '<link rel="canonical"' not in s or 'application/ld+json' not in s: errors.append("Missing SEO/JSON-LD: "+str(p))
 if "tobemotif-app-discovery" in s: errors.append("Old website URL: "+str(p))
 if APP["package_id"] not in s: errors.append("Missing package id: "+str(p))
 if ((p.parent.parent==DIST) or any(x in p.parts for x in ("tips","blog","guide","comparison")) or ("features" in p.parts and p.parent.name!="features")) and '<meta name="robots" content="noindex,follow">' not in s: errors.append("Thin page must stay noindex: "+str(p))
for c in STR["published_locales"]:
 for tail in ("","about","features","download","faq","tips","blog","guide","comparison"):
  p=DIST/c.lower()/tail/"index.html"
  if not p.is_file(): errors.append("Missing route: "+str(p))
  else:
   s=p.read_text()
   if f'<html lang="{c}"' not in s: errors.append("Wrong language: "+str(p))
   expected=BASE+"/"+c.lower()+("/about/" if tail=="" else "/"+tail+"/")
   if f'<link rel="canonical" href="{expected}">' not in s: errors.append("Wrong canonical: "+str(p))
try:
 ns="{http://www.sitemaps.org/schemas/sitemap/0.9}"; root=ET.parse(DIST/"sitemap.xml").getroot(); urls=[n.findtext(ns+"loc") for n in root.findall(ns+"url")]; txt=[x.strip() for x in (DIST/"sitemap.txt").read_text().splitlines() if x.strip()]
 if len(urls)!=len(set(urls)) or set(urls)!=set(txt): errors.append("Sitemap URLs are duplicated or XML/text differ")
 if len(urls)!=len(STR["published_locales"])*4: errors.append("Sitemap must contain only the four indexable core pages per locale")
 if any(u.rstrip("/").split("/")[-1] in [c.lower() for c in STR["published_locales"]] or any("/"+h+"/" in u for h in ("tips","blog","guide","comparison")) or ("/features/" in u and u.rstrip("/").split("/")[-1]!="features") for u in urls): errors.append("Noindex thin pages must not appear in the sitemap")
 if not all(u.endswith("/about/") or u.endswith("/features/") or u.endswith("/download/") or u.endswith("/faq/") for u in urls): errors.append("Sitemap contains a non-core page")
 if any(not u.startswith(BASE+"/") for u in urls): errors.append("Non-canonical URL in sitemap")
except Exception as ex: errors.append("Invalid sitemap: "+str(ex))
robots=(DIST/"robots.txt").read_text()
if f"Sitemap: {BASE}/sitemap.xml" not in robots or f"Sitemap: {BASE}/sitemap.txt" not in robots: errors.append("robots.txt sitemap directives missing")
if errors: print("\n".join(errors)); sys.exit(1)
print(f"Validated {len(urls)} sitemap routes across {len(STR['published_locales'])} locales.")
