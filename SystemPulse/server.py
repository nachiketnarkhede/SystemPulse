import os,json,time,threading,csv,io
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import psutil
from agent.collectors import sample,top_processes,devices,connections
from agent.analyzer import Engine
HOST='127.0.0.1';PORT=8000;WEB=os.path.join(os.path.dirname(__file__),'web');lock=threading.RLock();eng=Engine()
S={'telemetry':{},'top':[],'devices':[],'connections':[],'device_events':[],'research':False,'rows':[],'agent':{'status':'OBSERVING','message':'Initializing system intelligence...','last':None}}
def telemetry_worker():
 pd=psutil.disk_io_counters();pn=psutil.net_io_counters();pt=time.time()
 while True:
  try:
   d,pd,pn,pt=sample(pd,pn,pt);eng.ingest(d)
   with lock:
    S['telemetry']=d
    if S['research']:S['rows'].append({'timestamp':d['timestamp'],'cpu':d['cpu'],'ram':d['ram'],'disk_read_mb':d['disk_read_mb'],'disk_write_mb':d['disk_write_mb'],'network_down_mb':d['network_down_mb'],'network_up_mb':d['network_up_mb'],'wifi_signal':d['wifi'].get('signal'),'wifi_rx_mbps':d['wifi'].get('rx_mbps'),'wifi_tx_mbps':d['wifi'].get('tx_mbps')})
   time.sleep(.5)
  except Exception:time.sleep(1)
def worker(fn,key,delay):
 while True:
  try:
   x=fn()
   with lock:S[key]=x
  except:pass
  time.sleep(delay)
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=WEB,**k)
 def js(self,x,code=200):
  b=json.dumps(x,default=str).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path);path=p.path
  if path=='/api/telemetry':
   with lock:self.js({**S['telemetry'],'top_processes':S['top'],'agent':S['agent']});return
  if path=='/api/intelligence':
   with lock:d=S['telemetry'].copy();top=S['top'][:];dev=S['devices'][:];de=S['device_events'][:]
   obs=[];sev='NORMAL'
   if d:
    if d['cpu']>=90:obs.append('CPU utilization is very high.');sev='ELEVATED'
    elif d['cpu']>=70:obs.append('CPU activity is elevated.');sev='WATCH'
    if d['ram']>=92:obs.append('Memory utilization is very high.');sev='ELEVATED'
    elif d['ram']>=75:obs.append('Memory utilization is elevated.')
    if d['disk_read_mb']+d['disk_write_mb']>=60:obs.append('High disk I/O burst detected.');sev='WATCH' if sev=='NORMAL' else sev
    if not obs:obs=['Current telemetry appears stable.']
   else:obs=['Starting telemetry...']
   self.js({'condition':sev,'observations':obs,'events':list(eng.events)[-60:],'device_events':de[-40:],'top_processes':top});return
  if path=='/api/devices':
   with lock:self.js({'devices':S['devices'],'events':S['device_events'][-50:]});return
  if path=='/api/agent':
   q=parse_qs(p.query).get('q',[''])[0].strip()
   with lock:d=S['telemetry'].copy();top=S['top'][:];dev=S['devices'][:];con=S['connections'][:];S['agent']['status']='ANALYZING'
   if not d:self.js({'answer':'Telemetry is still initializing. Try again in a moment.'});return
   r=eng.answer(q,d,top,dev,con)
   with lock:S['agent']={'status':'OBSERVING','message':r['assessment'],'last':r}
   self.js(r);return
  if path=='/api/research/status':
   with lock:self.js({'active':S['research'],'samples':len(S['rows'])});return
  if path=='/api/research/start':
   with lock:S['research']=True;S['rows']=[]
   self.js({'ok':True});return
  if path=='/api/research/stop':
   with lock:S['research']=False;n=len(S['rows'])
   self.js({'ok':True,'samples':n});return
  if path=='/api/research/csv':
   with lock:rows=S['rows'][:]
   out=io.StringIO();fields=list(rows[0]) if rows else ['timestamp','cpu','ram'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader();w.writerows(rows);b=out.getvalue().encode();self.send_response(200);self.send_header('Content-Type','text/csv');self.send_header('Content-Disposition','attachment; filename="systempulse_research.csv"');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  if path=='/api/report':
   with lock:r={'generated_at':time.time(),'telemetry':S['telemetry'],'top_processes':S['top'],'devices':S['devices'],'connections':S['connections'],'events':list(eng.events)[-100:],'research_samples':len(S['rows'])}
   self.js(r);return
  if path=='/':self.path='/index.html'
  return super().do_GET()
if __name__=='__main__':
 threading.Thread(target=telemetry_worker,daemon=True).start();threading.Thread(target=worker,args=(lambda:top_processes(8),'top',2),daemon=True).start();threading.Thread(target=worker,args=(devices,'devices',5),daemon=True).start();threading.Thread(target=worker,args=(connections,'connections',3),daemon=True).start();print(f'SystemPulse: http://{HOST}:{PORT}');ThreadingHTTPServer((HOST,PORT),H).serve_forever()
