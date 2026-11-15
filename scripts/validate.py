#!/usr/bin/env python3
import json,pathlib,sys,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]; DIST=ROOT/"dist"
app=json.loads((ROOT/"content/app.json").read_text(encoding="utf-8"))
required=[DIST/"index.html",DIST/"robots.txt",DIST/"sitemap.xml",DIST/"llms.txt"]
for lang in ("en","ar"):
 for section in ("","about","features","faq"):
  required.append(DIST/lang/section/"index.html" if section else DIST/lang/"index.html")
errors=[]
for p in required:
 if not p.is_file(): errors.append(f"Missing generated file: {p.relative_to(DIST)}")
for p in required:
 if p.name=="index.html" and p.parent==DIST: continue
 if p.suffix==".html" and p.exists():
  s=p.read_text(encoding="utf-8")
  for token in ("canonical","hreflang","application/ld+json","Job Connect"):
   if token not in s: errors.append(f"{p.relative_to(DIST)} missing {token}")
if (DIST/"sitemap.xml").exists():
 try:
  root=ET.parse(DIST/"sitemap.xml").getroot()
  locs=[x.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text for x in root]
  if len(locs)!=8 or len(set(locs))!=len(locs): errors.append("Sitemap must contain 8 unique localized URLs")
 except ET.ParseError as ex: errors.append(f"Invalid sitemap XML: {ex}")
robots=DIST/"robots.txt"
if robots.exists() and "Sitemap: "+app["website_url"].rstrip("/")+"/sitemap.xml" not in robots.read_text(encoding="utf-8"):
 errors.append("robots.txt is missing the canonical sitemap location")
llms=DIST/"llms.txt"
if llms.exists() and "Job Connect" not in llms.read_text(encoding="utf-8"):
 errors.append("llms.txt is missing the app identity")
if app["package_id"] not in app["google_play_url"]: errors.append("Google Play URL/package ID mismatch")
if errors: print("\n".join(errors)); sys.exit(1)
print(f"Validated {len(required)} required files; bilingual pages, metadata, sitemap and app identity OK.")
