import re,difflib
from collections import Counter,deque
INTENTS={'cpu':['cpu','processor','processing','processor usage','cpu usage','cpu load'],'memory':['ram','memory','memory usage','available memory','out of memory'],'disk':['disk','storage','drive','disk activity','file transfer'],'wifi':['wifi','wi-fi','wireless','signal','ssid','router'],'network':['internet','network','latency','ping','download','upload','packet'],'device':['device','hardware','usb','keyboard','mouse','bluetooth','camera'],'security':['security','risk','vulnerability','danger','suspicious','attack','unsafe','threat','malware'],'performance':['slow','slower','lag','lagging','crawling','freeze','freezing','performance','heavy','weird','suddenly','spike','spiking'],'action':['what should i do','how can i fix','how do i fix','recommend','suggest','next step'],'explanation':['why','what happened','explain','cause','reason','what is happening']}
def norm(s):return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9\s-]',' ',s.lower())).strip()
def intents(q):
 q=norm(q); toks=set(q.split()); scores=Counter()
 for name,phrases in INTENTS.items():
  for p in phrases:
   p=norm(p)
   if p in q:scores[name]+=3 if ' ' in p else 2;continue
   ov=len(toks.intersection(p.split()));scores[name]+=ov
   for t in p.split():
    if len(t)>3 and difflib.get_close_matches(t,toks,n=1,cutoff=.84):scores[name]+=.5
 return [k for k,v in scores.most_common() if v>=2][:5],scores
class Engine:
 def __init__(self):self.cpu=deque(maxlen=120);self.ram=deque(maxlen=120);self.events=deque(maxlen=200)
 def ingest(self,d):
  self.cpu.append(d['cpu']);self.ram.append(d['ram']);disk=d['disk_read_mb']+d['disk_write_mb']
  if len(self.cpu)>10:
   b=sum(list(self.cpu)[-10:-1])/9
   if d['cpu']-b>=35:self.events.append({'timestamp':d['timestamp'],'type':'CPU_DEVIATION','message':f'CPU rose sharply relative to recent baseline ({b:.1f}% -> {d["cpu"]:.1f}%).'})
  if disk>=60:self.events.append({'timestamp':d['timestamp'],'type':'DISK_BURST','message':f'High disk activity observed ({disk:.2f} MB/s).'})
  if d['ram']>=92:self.events.append({'timestamp':d['timestamp'],'type':'MEMORY_PRESSURE','message':f'Memory utilization is very high ({d["ram"]:.1f}%).'})
 def answer(self,q,d,top=None,dev=None,conns=None):
  its,scores=intents(q);its=its or ['performance','explanation'];ev=[];rec=[];cpu=d['cpu'];ram=d['ram'];disk=d['disk_read_mb']+d['disk_write_mb'];net=d['network_down_mb']+d['network_up_mb'];sig=d['wifi'].get('signal');conf='HIGH'
  if 'cpu' in its or 'performance' in its:ev += [f'CPU utilization: {cpu:.1f}%',f'RAM utilization: {ram:.1f}%',f'Disk I/O: {disk:.2f} MB/s',f'Network traffic: {net:.2f} MB/s']
  if 'wifi' in its:ev += [f'Wi-Fi state: {d["wifi"].get("state")}',f'Wi-Fi signal: {sig if sig is not None else "Unavailable"}%',f'Wi-Fi RX: {d["wifi"].get("rx_mbps") or "Unavailable"} Mbps',f'Wi-Fi TX: {d["wifi"].get("tx_mbps") or "Unavailable"} Mbps']
  if 'device' in its:ev.append(f'OS-exposed devices: {len(dev or [])}')
  if 'security' in its:
   assessment='SystemPulse found observations worth reviewing, but telemetry alone does not prove compromise or a vulnerability.';rec=['Review the specific process, service, connection, or device behind the observation.','Treat anomalies as investigation leads, not automatic threat verdicts.'];conf='MEDIUM'
   if conns:ev.append(f'Network endpoints observed: {len(conns)}; a listening endpoint is not proof of a vulnerability.')
  elif cpu>=90:assessment='CPU activity is currently very high.';rec=['Inspect the process consuming CPU and decide whether its activity is expected.']
  elif ram>=92:assessment='Memory utilization is very high.';rec=['Inspect memory-heavy processes and available memory.']
  elif disk>=60:assessment='The current pattern is consistent with a storage I/O burst.';rec=['Correlate the burst with downloads, updates, or file transfers.']
  elif 'wifi' in its:
   assessment='Wi-Fi signal telemetry is unavailable.' if sig is None else ('The reported Wi-Fi signal is relatively weak.' if sig<40 else 'The reported Wi-Fi signal is currently usable.');rec=['Judge connection quality using signal, link rate, traffic, and latency together.']
  else:assessment='Current telemetry does not show a major abnormal condition.';rec=['Keep observing the timeline and ask again when the issue occurs.']
  if top and ('cpu' in its or 'performance' in its):ev.append(f'Top observed CPU process: {top[0]["name"]} (PID {top[0]["pid"]}, {top[0]["cpu"]:.1f}% CPU)');
  return {'answer':'\n'.join(['OBSERVATION',assessment,'','RELEVANT EVIDENCE']+[f'• {x}' for x in ev[:12]]+['','RECOMMENDATION']+[f'• {x}' for x in rec[:5]]+['',f'CONFIDENCE: {conf}']),'assessment':assessment,'confidence':conf,'intents':its,'scores':dict(scores),'evidence':ev,'recommendations':rec}
