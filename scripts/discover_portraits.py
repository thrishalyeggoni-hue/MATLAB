"""Collect public article lead-image filenames for a one-time, credited asset update."""
import concurrent.futures
import html
import json
import re
import time
import urllib.parse
from pathlib import Path
import httpx

ARTICLES={
'Charles Leclerc':'Charles_Leclerc','Max Verstappen':'Max_Verstappen','George Russell':'George_Russell_(racing_driver)',
'Carlos Sainz':'Carlos_Sainz_Jr.','Sergio Perez':'Sergio_Pérez','Fernando Alonso':'Fernando_Alonso',
'Lando Norris':'Lando_Norris','Oscar Piastri':'Oscar_Piastri','Lewis Hamilton':'Lewis_Hamilton',
'Nico Hulkenberg':'Nico_Hülkenberg','Lance Stroll':'Lance_Stroll','Yuki Tsunoda':'Yuki_Tsunoda',
'Alexander Albon':'Alex_Albon','Daniel Ricciardo':'Daniel_Ricciardo','Kevin Magnussen':'Kevin_Magnussen',
'Valtteri Bottas':'Valtteri_Bottas','Guanyu Zhou':'Zhou_Guanyu','Logan Sargeant':'Logan_Sargeant',
'Esteban Ocon':'Esteban_Ocon','Pierre Gasly':'Pierre_Gasly',
'Oliver Bearman':'Oliver_Bearman','Liam Lawson':'Liam_Lawson','Franco Colapinto':'Franco_Colapinto',
'Gabriel Bortoleto':'Gabriel_Bortoleto','Isack Hadjar':'Isack_Hadjar','Andrea Kimi Antonelli':'Andrea_Kimi_Antonelli','Jack Doohan':'Jack_Doohan'}

def discover(item):
 name,article=item
 try:
  with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'F1DriverDNA/1.0 (personal educational local website; image attribution included)'}) as client:
   r=client.get('https://en.wikipedia.org/wiki/'+urllib.parse.quote(article));r.raise_for_status()
  match=re.search(r'<meta property="og:image" content="([^"]+)"',r.text)
  if not match:return {'name':name,'error':'No lead image'}
  image=html.unescape(match[1]);path=urllib.parse.urlsplit(image).path
  parts=path.split('/');index=parts.index('thumb')
  filename=urllib.parse.unquote(parts[index+3])
  original='https://upload.wikimedia.org/wikipedia/commons/'+ '/'.join(parts[index+1:index+4])
  time.sleep(.5)
  return {'name':name,'filename':filename,'image_url':original,'source':'https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(filename),'article':str(r.url)}
 except Exception as exc:return {'name':name,'error':str(exc)}

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  rows=list(pool.map(discover,ARTICLES.items()))
 Path('reference/portrait-discovery.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
 for r in rows:print(r['name'],r.get('filename',r.get('error')),flush=True)
