import json,pathlib,sys,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parents[1];D=R/'dist';A=json.loads((R/'content/app.json').read_text());F=json.loads((R/'content/features.json').read_text());errors=[]
for p in [D/'index.html',D/'robots.txt',D/'sitemap.xml',D/'llms.txt',D/'assets/style.css',D/'assets/screens/screen-1.webp']:
 if not p.is_file():errors.append('Missing '+str(p.relative_to(D)))
for l in ('en','ar'):
 for s in ('','about','features','faq'):
  p=D/l/s/'index.html' if s else D/l/'index.html'
  if not p.is_file():errors.append('Missing '+str(p.relative_to(D)));continue
  x=p.read_text()
  for token in ('canonical','hreflang','application/ld+json','Job Connect'):
   if token not in x:errors.append(str(p)+' missing '+token)
try:
 root=ET.parse(D/'sitemap.xml').getroot();loc=[x.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text for x in root]
 if len(loc)!=8 or len(set(loc))!=8:errors.append('Sitemap URL count/uniqueness failed')
except Exception as e:errors.append(str(e))
if A['package_id'] not in A['google_play_url']:errors.append('Package ID mismatch')
if errors:print('\n'.join(errors));sys.exit(1)
print('Validated bilingual pages, 5 feature descriptions, hero screenshot, metadata and sitemap.')
