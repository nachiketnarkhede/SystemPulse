import os,re,json,subprocess,time,platform
import psutil

def cmd(args,timeout=4):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,shell=False)
        return p.stdout,p.returncode
    except Exception:return "",-1

def wifi():
    if os.name!='nt': return {'connected':False,'ssid':None,'signal':None,'rx_mbps':None,'tx_mbps':None,'state':'unsupported'}
    out,code=cmd(['netsh','wlan','show','interfaces'])
    d={'connected':False,'ssid':None,'signal':None,'rx_mbps':None,'tx_mbps':None,'state':'unavailable'}
    for raw in out.splitlines():
        if ':' not in raw: continue
        k,v=raw.strip().split(':',1); k=k.lower().strip(); v=v.strip()
        if k=='state': d['state']=v; d['connected']=v.lower()=='connected'
        elif k=='ssid' and v:d['ssid']=v
        elif k=='signal':
            m=re.search(r'(\d+)',v); d['signal']=int(m.group(1)) if m else None
        elif k.startswith('receive rate'):
            m=re.search(r'([\d.]+)',v); d['rx_mbps']=float(m.group(1)) if m else None
        elif k.startswith('transmit rate'):
            m=re.search(r'([\d.]+)',v); d['tx_mbps']=float(m.group(1)) if m else None
    return d

def devices():
    if os.name!='nt': return []
    script='''Get-CimInstance Win32_PnPEntity | Where-Object {$_.Present -eq $true} | Select Name,Status,Manufacturer,PNPDeviceID,PNPClass | ConvertTo-Json -Compress'''
    out,code=cmd(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',script],8)
    if code!=0 or not out:return []
    try:r=json.loads(out); r=r if isinstance(r,list) else [r]
    except Exception:return []
    ans=[]
    for x in r:
        name=x.get('Name') or 'Unknown'; nl=name.lower(); pid=x.get('PNPDeviceID') or ''
        cat='CONNECTIVITY' if any(s in nl for s in ['wi-fi','wireless','ethernet','bluetooth']) else ('EXTERNAL' if any(s in nl for s in ['usb','keyboard','mouse','camera','headset','microphone']) else 'INTERNAL')
        ans.append({'category':cat,'name':name,'status':x.get('Status') or 'Unknown','manufacturer':x.get('Manufacturer') or 'Unknown','device_id':pid,'class':x.get('PNPClass') or ''})
    return sorted(ans,key=lambda x:(x['category'],x['name'].lower()))[:500]

def top_processes(limit=8):
    ps=[]
    for p in psutil.process_iter(['pid','name','memory_percent']):
        try:p.cpu_percent(None);ps.append(p)
        except:pass
    time.sleep(.15); out=[]
    for p in ps:
        try:out.append({'pid':p.info['pid'],'name':p.info.get('name') or 'Unknown','cpu':round(p.cpu_percent(None),1),'memory':round(float(p.info.get('memory_percent') or 0),2)})
        except:pass
    return sorted(out,key=lambda x:x['cpu'],reverse=True)[:limit]

def connections():
    try:cs=psutil.net_connections('inet')
    except:return []
    out=[]
    for c in cs[:200]:
        try:l=f'{c.laddr.ip}:{c.laddr.port}' if c.laddr else ''
        except:l=''
        try:r=f'{c.raddr.ip}:{c.raddr.port}' if c.raddr else ''
        except:r=''
        out.append({'local':l,'remote':r,'status':c.status,'pid':c.pid})
    return out

def sample(prev_disk,prev_net,prev_t):
    now=time.time(); dt=max(now-prev_t,.001); disk=psutil.disk_io_counters(); net=psutil.net_io_counters(); mem=psutil.virtual_memory()
    try:du=psutil.disk_usage(os.environ.get('SystemDrive','C:')+'\\').percent
    except:du=None
    d={'timestamp':now,'platform':platform.system(),'cpu':round(psutil.cpu_percent(None),1),'ram':round(mem.percent,1),'ram_available_gb':round(mem.available/1024**3,2),'disk_percent':du,'disk_read_mb':round(max(0,disk.read_bytes-prev_disk.read_bytes)/dt/1024**2,2),'disk_write_mb':round(max(0,disk.write_bytes-prev_disk.write_bytes)/dt/1024**2,2),'network_down_mb':round(max(0,net.bytes_recv-prev_net.bytes_recv)/dt/1024**2,2),'network_up_mb':round(max(0,net.bytes_sent-prev_net.bytes_sent)/dt/1024**2),'wifi':wifi()}
    return d,disk,net,now
