import json,pathlib,subprocess,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class SiteTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):subprocess.run([sys.executable,str(R/'scripts/build.py')],check=True);subprocess.run([sys.executable,str(R/'scripts/validate.py')],check=True)
 def test_google_site_verification_tag(self):
  s=(R/'dist/index.html').read_text(encoding='utf-8');self.assertIn('name="google-site-verification"',s);self.assertIn('8mOiNMu4Tn477yFaR-IWrNQGhdqH1TpF6NKKoN94Oms',s)
 def test_identity(self):
  a=json.loads((R/'content/app.json').read_text());self.assertEqual(a['name'],'Job Connect');self.assertIn(a['package_id'],a['google_play_url'])
 def test_routes(self):
  for l in ('en','ar'):
   for s in ('','about','features','faq'):self.assertTrue((R/'dist'/l/s/'index.html' if s else R/'dist'/l/'index.html').is_file())
 def test_screenshot(self):self.assertTrue((R/'dist/assets/screens/screen-1.webp').is_file())
 def test_no_old_brand(self):
  for p in (R/'dist').rglob('*.html'):self.assertNotIn('Mingle',p.read_text())
 def test_google_play_cta(self):
  for l in ('en','ar'):self.assertIn('play.google.com/store/apps/details?id=com.jobsearch.jobconnect.work.jobs.devimpact',(R/'dist'/l/'index.html').read_text())
if __name__=='__main__':unittest.main()
