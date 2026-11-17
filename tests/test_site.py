import json,pathlib,subprocess,sys,unittest,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
class SiteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  subprocess.run([sys.executable,str(ROOT/"scripts/build.py")],check=True)
  subprocess.run([sys.executable,str(ROOT/"scripts/validate.py")],check=True)
 def test_identity(self):
  a=json.loads((ROOT/"content/app.json").read_text()); self.assertEqual(a["package_id"],"com.celibataire.single.devimpact"); self.assertIn(a["package_id"],a["google_play_url"]); self.assertEqual(a["name"],"Célibataire: Rencontres & Chat"); self.assertNotIn("brand_name",a)
 def test_official_name_only(self):
  for p in (ROOT/"dist").rglob("*.html"):
   if p == ROOT/"dist/index.html": continue
   x=p.read_text(); self.assertNotIn("Single: Meet & Chat",x); self.assertIn("Célibataire: Rencontres &amp; Chat",x)
 def test_all_locales(self):
  s=json.loads((ROOT/"content/market-strategy.json").read_text())
  for c in s["published_locales"]:
   for tail in ("","about","features","download","faq","tips","blog","guide","comparison"): self.assertTrue((ROOT/"dist"/c.lower()/tail/"index.html").is_file())
 def test_no_old_brand(self):
  for p in (ROOT/"dist").rglob("*.html"):
   x=p.read_text(); self.assertNotIn("Job Connect",x); self.assertNotIn("job search",x.lower())
 def test_sitemap(self):
  ns="{http://www.sitemaps.org/schemas/sitemap/0.9}"; root=ET.parse(ROOT/"dist/sitemap.xml").getroot(); urls=[n.findtext(ns+"loc") for n in root.findall(ns+"url")]; txt=[x for x in (ROOT/"dist/sitemap.txt").read_text().splitlines() if x]; self.assertEqual(set(urls),set(txt)); self.assertEqual(len(urls),len(set(urls)))
if __name__=="__main__": unittest.main()
