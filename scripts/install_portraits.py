"""Download original, individually reviewed Commons photos and generate attribution metadata.

No photo is generated or retouched. Card framing and fades are CSS presentation.
Re-running only downloads missing local files; it never changes session participants.
"""
import hashlib
import json
import re
import time
import urllib.parse
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parent.parent
rows=json.loads((ROOT/'reference/portrait-discovery.json').read_text())
CREDITS={
'Charles Leclerc':('Gilzetbase; source crop by DaanTW','CC BY-SA 4.0',2020),
'Max Verstappen':('Steffen Prößdorf','CC BY-SA 4.0',2024),
'George Russell':('Raph_PH','CC BY 2.0',2024),
'Carlos Sainz':('Luca Fazzolari / WikiPortraits','CC BY-SA 4.0',2026),
'Sergio Perez':('XaviYuahanda','CC BY-SA 4.0',2019),
'Fernando Alonso':('United Autosports / Jakob Ebrey','CC BY-SA 2.0',2017),
'Lando Norris':('Steffen Prößdorf','CC BY-SA 4.0',2024),
'Oscar Piastri':('Liauzh','CC BY 4.0',2026),
'Lewis Hamilton':('Lauren Hurley / No 10 Downing Street; Crown copyright','OGL v3.0',2025),
'Nico Hulkenberg':('Marc Alvarado; source crop by Danyele','CC BY-SA 2.0',2019),
'Lance Stroll':('Liauzh','CC BY-SA 4.0',2025),
'Yuki Tsunoda':('Yu Chu Chin','CC BY-SA 4.0',2026),
'Alexander Albon':('Yu Chu Chin','CC BY-SA 4.0',2026),
'Daniel Ricciardo':('DaHuzyBru','CC BY-SA 4.0',2024),
'Kevin Magnussen':('Henry Mineur','CC BY-SA 3.0',2012),
'Valtteri Bottas':('Yu Chu Chin','CC BY-SA 4.0',2026),
'Guanyu Zhou':('Yu Chu Chin','CC BY-SA 4.0',2026),
'Logan Sargeant':('Joe Schilp / JazzyJoeyD','CC BY-SA 4.0',2024),
'Esteban Ocon':('Rrtb505050','CC0 1.0',2024),
'Pierre Gasly':('Morio','CC BY-SA 4.0',2017),
'Oliver Bearman':('Liauzh','CC BY-SA 4.0',2025),
'Liam Lawson':('Yu Chu Chin','CC BY-SA 4.0',2026),
'Isack Hadjar':('Yu Chu Chin','CC BY-SA 4.0',2026),
}
OVERRIDES={'Charles Leclerc':'Charles_Leclerc_portrait_2020.png',
'Nico Hulkenberg':'2019_Formula_One_tests_Barcelona,_Hulkenberg_(40287128313)_(headshot).jpg',
'Kevin Magnussen':'Kevin_Magnussen_2012-1.JPG'}
LICENSES={
'CC BY-SA 4.0':'https://creativecommons.org/licenses/by-sa/4.0/',
'CC BY-SA 3.0':'https://creativecommons.org/licenses/by-sa/3.0/',
'CC BY-SA 2.0':'https://creativecommons.org/licenses/by-sa/2.0/',
'CC BY 2.0':'https://creativecommons.org/licenses/by/2.0/',
'CC BY 4.0':'https://creativecommons.org/licenses/by/4.0/',
'CC0 1.0':'https://creativecommons.org/publicdomain/zero/1.0/',
'OGL v3.0':'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'}
output=[]
folder=ROOT/'frontend/public/portraits';folder.mkdir(exist_ok=True)
with httpx.Client(timeout=60,follow_redirects=True,headers={'User-Agent':'F1DriverDNA/1.0 (personal educational local website; image attribution included)'}) as client:
 for row in rows:
  name=row['name']
  if name not in CREDITS:continue
  filename=OVERRIDES.get(name,row.get('filename'))
  if not filename:continue
  filename=filename.replace(' ','_')
  digest=hashlib.md5(filename.encode()).hexdigest()
  url=f'https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{urllib.parse.quote(filename)}'
  slug=re.sub('[^a-z0-9]+','-',name.lower()).strip('-')
  target=folder/(slug+Path(filename).suffix.lower())
  if not target.exists():
   response=client.get(url)
   if response.status_code==429:
    print('RATE LIMITED — stop downloading; retry after',response.headers.get('Retry-After','a few minutes'),flush=True)
    break
   if response.status_code!=200 or not response.headers.get('content-type','').startswith('image/'):
    print('UNAVAILABLE',name,response.status_code,flush=True);continue
   target.write_bytes(response.content)
   time.sleep(5)
  author,license_name,year=CREDITS[name]
  output.append({'name':name,'src':'/portraits/'+target.name,'author':author,'license':license_name,'licenseUrl':LICENSES[license_name],
    'source':'https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(filename),'originalUrl':url,'photoYear':year,
    'position':'50% 24%','changes':'Original source file retained. Display uses CSS cropping, colour treatment, and edge fading; no facial retouching or generated imagery.'})
  print('INSTALLED',name,target.stat().st_size,flush=True)
(ROOT/'frontend/src/portrait-catalog.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
(folder/'credits.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
print('TOTAL',len(output),flush=True)
