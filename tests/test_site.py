import json,pathlib,subprocess,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class SiteBuildTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  subprocess.run([sys.executable,str(ROOT/"scripts/build.py")],check=True)
  subprocess.run([sys.executable,str(ROOT/"scripts/validate.py")],check=True)
 def test_store_identity(self):
  app=json.loads((ROOT/"content/app.json").read_text(encoding="utf-8"))
  self.assertEqual(app["name"],"Job Connect")
  self.assertEqual(app["package_id"],"com.jobsearch.jobconnect.work.jobs.devimpact")
  self.assertIn(app["package_id"],app["google_play_url"])
 def test_all_localized_routes_exist(self):
  for lang in ("en","ar"):
   for section in ("","about","features","faq"):
    p=ROOT/"dist"/lang/section/"index.html" if section else ROOT/"dist"/lang/"index.html"
    self.assertTrue(p.is_file(),str(p))
 def test_no_previous_branding(self):
  for p in (ROOT/"dist").rglob("*.html"):
   self.assertNotIn("Min"+"gle",p.read_text(encoding="utf-8"))
 def test_store_link_on_homepages(self):
  for lang in ("en","ar"):
   s=(ROOT/"dist"/lang/"index.html").read_text(encoding="utf-8")
   self.assertIn("play.google.com/store/apps/details?id=com.jobsearch.jobconnect.work.jobs.devimpact",s)
if __name__=="__main__": unittest.main()
