"""Archivo incremental de Global Brain en ORIA. Solo consume datos, nunca código remoto."""
import argparse,collections,datetime,hashlib,json,os,re,shutil,subprocess,sys,urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

URL='https://covid-production-7835.up.railway.app'
AREA='Global Brain';MARK='global-brain-generado'
def sha(b):return hashlib.sha256(b).hexdigest()
def text(value):return str(value.get('es') or value.get('en') or '') if isinstance(value,dict) else str(value or '')
def wiki(rel,label=None):return '[['+Path(rel).with_suffix('').as_posix()+('|' + label if label else '')+']]'
def safe(value):return re.sub(r'[\\/:*?"<>|]','-',str(value)).strip(' .')[:110]
def get_json(url):
 url+=('&' if '?' in url else '?')+'oria_corte='+str(datetime.datetime.now(datetime.timezone.utc).timestamp())
 req=urllib.request.Request(url,headers={'User-Agent':'ORIA-GlobalBrain-Archive/1.0','Cache-Control':'no-cache'})
 with urllib.request.urlopen(req,timeout=45) as response:
  if response.status!=200:raise RuntimeError('Respuesta HTTP incompleta')
  blob=response.read(10*1024*1024+1)
 if len(blob)>10*1024*1024:raise ValueError('Archivo supera el límite de lectura')
 return json.loads(blob.decode('utf-8-sig')),blob
def validate_pulse(data):
 meta=data.get('meta',{});date=meta.get('fecha','');datetime.date.fromisoformat(date)
 if meta.get('modo')!='live':raise ValueError('No se importa un reporte de demostración')
 if not isinstance(data.get('nodos'),list):raise ValueError('Reporte incompleto')
 if meta.get('schema') == '2.0':
  md=data.get('reporte_markdown','')
  if not md.startswith('---\n') or '# Pulso Global — '+date not in md:raise ValueError('Falta el reporte canónico')
  if sha(md.encode('utf-8')) != meta.get('reporte_sha256'):raise ValueError('Markdown con huella incompatible')
 elif not data['nodos']:raise ValueError('Reporte vacío o incompleto')
 ids=[n['id'] for n in data['nodos']]
 if len(set(ids))!=len(ids):raise ValueError('IDs repetidos')
 for n in data['nodos']:
  if not text(n.get('titulo')) or not isinstance(n.get('referencias'),list):raise ValueError('Noticia incompleta')
 return date
def report_md(pulse,trends=None):
 date=validate_pulse(pulse)
 if pulse.get('meta',{}).get('schema') == '2.0':return pulse['reporte_markdown']
 nodes=sorted(pulse['nodos'],key=lambda n:n.get('impacto') or 0,reverse=True)
 lines=[f'# Global Brain — Reporte {date}','',f"**{len(nodes)} noticias.** Edición publicada por [Global Brain]({URL}/).",'',f"Generado por la aplicación: `{pulse['meta'].get('generado','')}`.",'','Las síntesis, categorías y puntuaciones siguientes proceden de la aplicación. Su estado «verificado» significa que la app registró referencias; no acredita una comprobación independiente de todos los hechos.','']
 for n in nodes:
  lines += ['## '+text(n['titulo']),'',text(n.get('sintesis')),'',f"Categoría: **{n['categoria']}** · Impacto de la app: **{n.get('impacto') if n.get('impacto') is not None else 'sin puntuación'}**",'','### Fuentes','']
  for r in n['referencias']:
   url=r.get('url','')
   if url.startswith(('https://','http://')):lines.append('- ['+str(r.get('fuente') or 'Fuente')+']('+url+') — '+str(r.get('titulo') or '')+' · '+str(r.get('fecha') or ''))
  lines.append('')
 if trends:
  lines += ['## Tendencias publicadas con esta edición','',f"Ventana de la app: **{trends['meta'].get('ventana_dias')} días**. Captura: `{trends['meta'].get('generado')}`.",'']
  for t in trends.get('temas',[]):
   lines += ['### '+text(t['nombre']),'',text(t.get('resumen')),'',text(t.get('estado')),'','| Fecha | Noticias | Impacto máximo de la app |','| --- | ---: | ---: |']
   for s in t.get('serie',[]):lines.append(f"| {s['fecha']} | {s['n']} | {s['max']} |")
   lines += ['','#### Noticias de esta tendencia','']
   for n in t.get('nodos',[]):
    title=text(n.get('titulo'));url=n.get('url','');label='['+title+']('+url+')' if url.startswith(('http://','https://')) else title
    lines.append('- '+str(n.get('fecha',''))+' — '+label+' · '+str(n.get('fuente','')))
   lines.append('')
 else:lines+=['## Tendencias de esta edición','','No se recuperó una captura de tendencias correspondiente a este día. No se reconstruyó ni se sustituyó por las tendencias actuales.','']
 lines += [wiki(AREA+'/00 Global Brain')+' · '+wiki('Aplicaciones/Pulso Global'),'']
 return '\n'.join(lines)
def main():
 p=argparse.ArgumentParser();p.add_argument('--oria',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--historial-root',type=Path);p.add_argument('--actualizar',action='store_true');p.add_argument('--indexar',action='store_true');a=p.parse_args()
 cfg=json.loads((a.oria/'oria.config.json').read_text(encoding='utf-8-sig'));vault=Path(cfg['boveda']);assert vault.is_dir() and (vault/'00 Oria.md').is_file()
 now=datetime.datetime.now(ZoneInfo('America/New_York'));today=now.date().isoformat();lot=a.oria/'registro/global-brain'/now.strftime('%Y%m%d-%H%M%S-%f');lot.mkdir(parents=True,exist_ok=True);changes=[];warnings=[]
 lockpath=a.oria/'registro/global-brain/importacion.lock'
 try:lockfd=os.open(lockpath,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise RuntimeError('Hay una importación activa; no se inicia otra')
 os.close(lockfd)
 def put(rel,body,managed=False):
  target=vault/rel;blob=body.encode('utf-8') if isinstance(body,str) else body;before=target.read_bytes() if target.exists() else None
  original_before=before
  if managed:
   # Preserve the canonical source verbatim; annotations remain in the existing note.
   canonical=blob.decode('utf-8')
   if canonical.startswith('---\n') and 'tipo: "pulso-global"' in canonical.split('\n---\n',1)[0]:
    front,bodytext=canonical.split('\n---\n',1)
    keys={line.split(':',1)[0] for line in front.splitlines()[1:] if ':' in line}
    if before:
     previous=before.decode('utf-8-sig')
     if previous.startswith(('---\n','---\r\n')):
      oldfront,oldbody=re.split(r'\r?\n---\r?\n',previous,maxsplit=1)
      extras=[line for line in oldfront.splitlines()[1:] if line.split(':',1)[0] not in keys]
      before=(front+'\n'+'\n'.join(extras)+'\n---\n'+oldbody).encode('utf-8')
    else:
     before=(front+'\n---\n\n<!-- '+MARK+' -->\n<!-- /'+MARK+' -->\n\n## Mis notas\n\n').encode('utf-8')
    source=vault/AREA/'Fuentes'/re.search(r'\d{4}-\d{2}-\d{2}',rel).group()/'reporte.md'
    put(source.relative_to(vault).as_posix(),canonical)
    blob=bodytext.lstrip('\n').encode('utf-8')
   start='<!-- '+MARK+' -->';end='<!-- /'+MARK+' -->';generated=start+'\n'+blob.decode('utf-8').rstrip()+'\n'+end
   if before:
    previous=before.decode('utf-8-sig')
    if start not in previous or end not in previous:raise RuntimeError('Nota existente sin bloque administrado: '+rel)
    previous=previous[:previous.index(start)]+generated+previous[previous.index(end)+len(end):];blob=previous.encode('utf-8')
   else:blob=('---\ntipo: reporte-global-brain\nfecha: '+re.search(r'\d{4}-\d{2}-\d{2}',rel).group()+'\norigen: global-pulse\n---\n\n'+generated+'\n\n## Mis notas\n\n').encode('utf-8')
  before=original_before
  if before==blob:return
  if before is not None:
   backup=lot/'antes'/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before)
  target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.oria-temporal');tmp.write_bytes(blob);tmp.replace(target)
  if sha(target.read_bytes())!=sha(blob):raise RuntimeError('La escritura no coincide')
  changes.append({'ruta':rel,'antes':sha(before) if before is not None else None,'despues':sha(blob)})
 def block(rel,name,body):
  target=vault/rel;old=target.read_text(encoding='utf-8') if target.exists() else '';start='<!-- oria:'+name+' -->';end='<!-- /oria:'+name+' -->';fragment=start+'\n'+body.rstrip()+'\n'+end
  if start in old:
   if end not in old:raise RuntimeError('Bloque incompleto')
   old=old[:old.index(start)]+fragment+old[old.index(end)+len(end):]
  else:old=old.rstrip()+'\n\n'+fragment+'\n'
  put(rel,old)
 try:
  imported=0
  if a.historial_root:
   src=a.historial_root/'data';internal=src/'global-brain/Global Brain';files=list(internal.rglob('*.md'));names=collections.defaultdict(list)
   for f in files:names[f.stem].append(f.relative_to(internal).as_posix())
   for f in files:
    rel=f.relative_to(internal).as_posix();body=f.read_text(encoding='utf-8')
    def replace_link(match):
     value=match.group(1);parts=value.split('|',1);dest=parts[0];anchor=dest.split('#',1);hits=names.get(anchor[0],[])
     if len(hits)==1:
      destination=Path(AREA+'/Archivo de la app/'+hits[0]).with_suffix('').as_posix()+('#'+anchor[1] if len(anchor)>1 else '')
      return '[['+destination+'|'+(parts[-1] if len(parts)>1 else anchor[0])+']]'
     if len(hits)>1:return ' · '.join(wiki(AREA+'/Archivo de la app/'+h,parts[-1]) for h in hits)
     return parts[-1]
    body=re.sub(r'\[\[([^\]]+)\]\]',replace_link,body);body=body.replace('FROM "10 · Nodos"',f'FROM "{AREA}/Archivo de la app/10 · Nodos"')
    body+='\n\n'+wiki(AREA+'/00 Global Brain')+'\n'
    dest=AREA+'/Archivo de la app/'+rel
    if not (vault/dest).exists():put(dest,body)
   overview=['---','tipo: indice','---','','# Bóveda original de Global Brain','','Copia recuperada de la bóveda interna de la aplicación. Los datos y análisis históricos conservan las síntesis de la app; pueden contener errores originales.','']
   overview.extend('- '+wiki(AREA+'/Archivo de la app/'+f.relative_to(internal).as_posix(),f.stem) for f in sorted(files))
   overview+=['',wiki(AREA+'/00 Global Brain'),''];put(AREA+'/Archivo de la app/00 Archivo.md','\n'.join(overview))
   for f in sorted(src.glob('pulse-20*.json')):
    blob=f.read_bytes();data=json.loads(blob);date=validate_pulse(data);put(AREA+'/Fuentes/'+date+'/pulse-'+sha(blob)[:12]+'.json',blob)
    report_path=AREA+'/Reportes/Global Brain — Reporte '+date+'.md'
    if not (vault/report_path).exists():put(report_path,report_md(data),managed=True)
    imported+=1
  if a.actualizar:
   history,_=get_json(URL+'/data/history.json')
   if history.get('schema')!=1 or not isinstance(history.get('reportes'),list):raise ValueError('Historial público incompleto')
   for entry in history['reportes']:
    day=entry['fecha'];datetime.date.fromisoformat(day)
    if day>today:raise ValueError('Historial fechado en el futuro')
    if entry['archivo']!='pulse-'+day.replace('-','')+'.json':raise ValueError('Ruta de reporte inesperada')
    report_path=AREA+'/Reportes/Global Brain — Reporte '+day+'.md'
    if (vault/report_path).exists():continue
    archived,blob=get_json(URL+'/data/'+entry['archivo'])
    if sha(blob)!=entry['sha256'] or validate_pulse(archived)!=day:raise ValueError('La huella del historial no coincide')
    captured=None
    if entry.get('tendencias'):
     if entry['tendencias']!='trends-'+day.replace('-','')+'.json':raise ValueError('Ruta de tendencias inesperada')
     captured,capture_blob=get_json(URL+'/data/'+entry['tendencias'])
     if sha(capture_blob)!=entry['tendencias_sha256'] or captured.get('meta',{}).get('generado','')[:10]!=day:raise ValueError('Tendencias históricas incompatibles')
     put(AREA+'/Fuentes/'+day+'/trends-'+sha(capture_blob)[:12]+'.json',capture_blob)
    put(AREA+'/Fuentes/'+day+'/pulse-'+sha(blob)[:12]+'.json',blob)
    put(report_path,report_md(archived,captured),managed=True);imported+=1
   pulse,raw=get_json(URL+'/data/pulse-latest.json');date=validate_pulse(pulse)
   if date>today:raise ValueError('La edición está fechada en el futuro')
   trends,trendraw=get_json(URL+'/data/trends-latest.json');datetime.datetime.fromisoformat(trends['meta']['generado'])
   if trends.get('meta',{}).get('modo')!='live' or not isinstance(trends.get('temas'),list):raise ValueError('Tendencias incompletas')
   if trends['meta']['generado'][:10]!=date:
    warnings.append('Las tendencias no corresponden al día de la edición; se conserva la captura sin presentarla como actual.');trends_for_report=None
   else:trends_for_report=trends
   put(AREA+'/Fuentes/'+date+'/pulse-'+sha(raw)[:12]+'.json',raw);put(AREA+'/Fuentes/'+date+'/trends-'+sha(trendraw)[:12]+'.json',trendraw)
   put(AREA+'/Reportes/Global Brain — Reporte '+date+'.md',report_md(pulse,trends_for_report),managed=True)
   if date!=today:warnings.append('El servidor todavía no tiene la edición de hoy; no se inventó un reporte de hoy.')
  reports=sorted((vault/AREA/'Reportes').glob('*.md'),reverse=True);home=['---','tipo: portada de area','---','','# Global Brain','','Reportes acumulados de la aplicación, conectados con ORIA. Las notas personales quedan fuera del bloque generado y se conservan en futuras actualizaciones.','',f'**{len(reports)} reportes diarios recuperados.**','','## Historial','']
  for f in reports:home.append('- '+wiki(f.relative_to(vault).as_posix(),f.stem))
  home += ['', '## Archivo de la aplicación','',wiki(AREA+'/Archivo de la app/00 Archivo')+' · '+wiki('Aplicaciones/Pulso Global'),'','Las tendencias de 21 días publicadas por la app se guardan con cada nueva edición. Para días antiguos sin esa captura, se conserva el reporte diario y se indica la ausencia. No se fabrican tendencias históricas.','',wiki('00 Oria'),'']
  block(AREA+'/00 Global Brain.md','global-brain-portada','\n'.join(home));block('Aplicaciones/Pulso Global.md','global-brain-reportes','## Reportes e historial\n\nGlobal Brain publica noticias agrupadas, fuentes y tendencias. '+wiki(AREA+'/00 Global Brain','Abrir el historial acumulado')+'\n\nLa ficha de la aplicación es distinta del contenido de los reportes. Los reportes y la bóveda interna se incorporan aquí mediante el archivo diario.');block('00 Oria.md','global-brain-reportes','## Global Brain\n\n'+wiki(AREA+'/00 Global Brain','Reportes, fuentes e historial de Global Brain'))
  report={'fecha':now.isoformat(),'boveda':str(vault),'historial_recuperado':imported,'reportes_acumulados':len(reports),'cambios':changes,'advertencias':warnings,'estado':'incorporado'}
  manifest=lot/'manifiesto.json'
  manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  if a.indexar and any(c['ruta'].endswith('.md') for c in changes):
   env=dict(os.environ,PYTHONIOENCODING='utf-8')
   result=subprocess.run([sys.executable,'-m','conocimiento.sincronizacion'],cwd=a.oria,capture_output=True,text=True,encoding='utf-8',env=env)
   (lot/'indexacion.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
   if result.returncode:raise RuntimeError('Contenido incorporado; indexación rechazada. Ver '+str(lot/'indexacion.txt'))
   control=json.loads(result.stdout)
   if not control.get('publicado'):raise RuntimeError('El índice no se publicó')
   report['indexacion']={'estado':control.get('estado'),'publicado':True}
   manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({'reportes':len(reports),'archivos_cambiados':len(changes),'advertencias':warnings,'manifiesto':str(manifest),'indexacion':report.get('indexacion')},ensure_ascii=False))
 except Exception as exc:
  (lot/'error.json').write_text(json.dumps({'estado':'error','motivo':str(exc),'cambios':changes},ensure_ascii=False,indent=2),encoding='utf-8')
  raise
 finally:lockpath.unlink(missing_ok=True)
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as exc:print(json.dumps({'estado':'error','motivo':str(exc)},ensure_ascii=False));sys.exit(1)
