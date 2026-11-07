"""Automated checks for Aasmaan (65 of them). Open-Meteo is SIMULATED with mock responses, so this tests the app logic, not the live service.
Setup:  pip install playwright astral && playwright install chromium
Run:    python3 tests/test_app.py
"""
import os,json,math,threading,http.server,socketserver,functools,re,sys,traceback
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
socketserver.TCPServer.allow_reuse_address=True
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','web'));H.log_message=lambda *a:None
threading.Thread(target=socketserver.TCPServer(('127.0.0.1',8820),H).serve_forever,daemon=True).start()
dates=[f"2026-11-{i:02d}" for i in range(1,9)];hrs=[f"{d}T{h:02d}:00" for d in dates for h in range(24)]
DEF=dict(hi=[29,28,27,22,25,27,28],lo=[14,13,14,15,13,12,12],code=[1,0,2,3,3,0,1],pp=[10,5,20,30,30,5,0],ps=[0,0,2,5,5,0,0],uv=[5]*7,gust=22,aqi=132,dust=20,vis=lambda i:20000,prob=lambda i:5,off=False)
D=dict(DEF)
def reset():D.clear();D.update(DEF)
def one(k=0):
    tp=[round(D['lo'][min(i//24,6)]+(D['hi'][min(i//24,6)]-D['lo'][min(i//24,6)])*(.5+.5*math.sin((i%24-9)/24*6.283))+k*.1,1) for i in range(len(hrs))]
    return {"current":{"temperature_2m":28.1,"apparent_temperature":26.7,"relative_humidity_2m":34,"weather_code":1,"wind_speed_10m":9.5,"wind_direction_10m":315,"wind_gusts_10m":D['gust']},
    "hourly":{"time":hrs,"temperature_2m":tp,"precipitation":[0]*len(hrs),"precipitation_probability":[D['prob'](i) for i in range(len(hrs))],"wind_speed_10m":[10]*len(hrs),"visibility":[D['vis'](i) for i in range(len(hrs))]},
    "daily":{"time":dates[:7],"weather_code":D['code'],"temperature_2m_max":D['hi'],"temperature_2m_min":D['lo'],"sunrise":[d+"T06:26" for d in dates[:7]],"sunset":[d+"T17:09" for d in dates[:7]],"uv_index_max":D['uv'],"precipitation_probability_max":D['pp'],"precipitation_sum":D['ps']}}
reqs=[]
def api(r):
    u=r.request.url;h={'access-control-allow-origin':'*'};reqs.append(u)
    if D['off']:return r.abort()
    q=parse_qs(urlparse(u).query)
    if 'geocoding' in u:
        n=q.get('name',[''])[0].lower();ur=q.get('language',['en'])[0]=='ur'
        return r.fulfill(json={"results":[{"id":7,"name":"سیالکوٹ" if ur else "Sialkot","latitude":32.5,"longitude":74.53,"admin1":"Punjab","country":"Pakistan"}]} if n.startswith('sial') else {},headers=h)
    if 'air-quality' in u:return r.fulfill(json={"current":{"us_aqi":D['aqi'],"pm2_5":48,"dust":D['dust']}},headers=h)
    if 'past_days' in u or 'archive' in u:return r.fulfill(json={"daily":{"temperature_2m_max":[27.1,29]}},headers=h)
    n=len(q['latitude'][0].split(','));d=[one(k) for k in range(n)];r.fulfill(json=d if n>1 else d[0],headers=h)
clock="(()=>{const R=Date,off=R.UTC(2026,10,1,9,20)-R.now();class D extends R{constructor(...a){a.length?super(...a):super(R.now()+off)}static now(){return R.now()+off}}window.Date=D})()"
res=[];errs=[]
def ok(n,c,x=''):
    res.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+((' | '+str(x)) if (x and not c) or x=='!' else ''))
with sync_playwright() as p:
    b=p.chromium.launch()
    def mk(w=390,geo=None):
        ctx=b.new_context(viewport={'width':w,'height':844},geolocation=geo,permissions=['geolocation','clipboard-read','clipboard-write'])
        ctx.add_init_script(clock);ctx.route("**/*open-meteo.com/**",api);ctx.route("**/fonts.g*/**",lambda r:r.abort())
        pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));return ctx,pg
    def load(pg,url='/index.html'):
        pg.goto('http://127.0.0.1:8820'+url);pg.wait_for_selector('#dial',timeout=15000);pg.wait_for_function("document.getElementById('splash').classList.contains('off')",timeout=15000);pg.wait_for_timeout(1100)
    def tool(pg,k):
        pg.click('#toolsBtn');pg.click(f'[data-k={k}]');pg.wait_for_timeout(500)
    def close(pg):pg.click('#pClose');pg.wait_for_timeout(300)
    def alerts(pg):return ' '.join(pg.locator('.alerts div').all_inner_texts()) if pg.locator('.alerts').count() else ''
    def T(name,f):
        try:f()
        except Exception as e:ok(name+' (crashed)',False,str(e)[:160]);traceback.print_exc(limit=1)
    BAD=r'\b(NaN|undefined|null|Infinity)\b'
    # ---------- 1 main screen ----------
    def t1():
        ctx,pg=mk();load(pg);ok('main: dial renders',pg.locator('#dial').count()==1)
        ok('main: no NaN/undefined/null on screen',not re.search(BAD,pg.inner_text('body')))
        ok('main: temperature shows 28°',pg.inner_text('#cT').strip()=='28°',pg.inner_text('#cT'))
        pg.click('[data-u=F]');pg.wait_for_timeout(300);ok('units: °F conversion (28.1°C = 83°F)',pg.inner_text('#cT').strip()=='83°',pg.inner_text('#cT'));ok('units: high/low in °F',('H 84°' in pg.inner_text('#cS')),pg.inner_text('#cS'))
        pg.click('[data-u=C]');pg.wait_for_timeout(300);ok('units: back to °C',pg.inner_text('#cT').strip()=='28°')
        bb=pg.locator('#dial').bounding_box();cx,cy=bb['x']+bb['width']/2,bb['y']+bb['height']/2;pg.mouse.move(cx-60,cy+40);pg.mouse.move(cx+50,cy-40);pg.wait_for_timeout(200)
        ok('dial scrub shows a time',re.search(r'\d+:\d\d (AM|PM)',pg.inner_text('#cL')) is not None,pg.inner_text('#cL'))
        ok('sun: sunrise/sunset shown',re.search(r'6:26',pg.inner_text('.sun')) and re.search(r'5:09',pg.inner_text('.sun')),pg.inner_text('.sun'))
        ok('sun: countdown text',re.search(r'(Sunrise|Sunset) in \d+h \d+m',pg.inner_text('body')) is not None)
        ok('extras: tip + rain strip + details',pg.locator('.tip').count()==1 and pg.locator('.rs').count()==1 and pg.locator('.det>div').count()==4)
        ok('history line shows',('Yesterday peaked' in pg.inner_text('body')))
        pg.mouse.move(5,5);pg.click('.rib button:nth-child(4)');pg.wait_for_timeout(400);ok('7-day: tapping a day redraws (Thu high 22°)',pg.inner_text('#cT').strip()=='22°',pg.inner_text('#cT'))
        pg.click('#shareBtn');pg.wait_for_timeout(500);ok('share copies forecast (no native share on desktop)','copied' in pg.inner_text('#toast').lower(),pg.inner_text('#toast'))
        ctx.close()
    T('main',t1)
    # ---------- 2 cities / search / remove ----------
    def t2():
        ctx,pg=mk();load(pg);C=pg.evaluate("CITIES.slice(0,12).map(c=>[c[0],c[2],c[3]])");bad=[]
        for i,c in enumerate(C):
            reqs.clear();pg.click('#cityBtn');pg.click(f'.grid button:nth-child({i+1})');pg.wait_for_timeout(500)
            f=[u for u in reqs if '/v1/forecast' in u and 'daily=' in u and 'hourly=temperature_2m,' in u]
            if pg.inner_text('#hEn').split(' ')[0]!=c[0] or not f or f'latitude={c[1]}' not in f[-1]:bad.append(c[0])
        ok('cities: all 12 load with the right coordinates',not bad,bad)
        pg.click('#cityBtn');pg.fill('#q','Sial');pg.wait_for_timeout(900);ok('search: finds Sialkot',pg.locator('#sr button').count()==1)
        pg.click('#sr button');pg.wait_for_timeout(700);ok('search: selects added city',pg.inner_text('#hEn').startswith('Sialkot'),pg.inner_text('#hEn'));ok('search: Urdu name used',pg.inner_text('#hUr').strip()=='سیالکوٹ',pg.inner_text('#hUr'))
        ok('search: saved to storage',len(json.loads(pg.evaluate("localStorage.getItem('cx')")))==1)
        pg.click('#cityBtn');pg.click('.grid .x');pg.wait_for_timeout(600);ok('remove: city deleted and app falls back',pg.evaluate("CITIES.length")==12 and pg.inner_text('#hEn').startswith('Peshawar'),pg.inner_text('#hEn'))
        ctx.close()
    T('cities',t2)
    def t3():
        ctx,pg=mk(geo={'latitude':31.52,'longitude':74.36});load(pg);pg.click('#cityBtn');pg.click('#loc');pg.wait_for_timeout(1500)
        ok('location: inside Pakistan -> My location',pg.inner_text('#hEn').startswith('My location'),pg.inner_text('#hEn'))
        ctx.set_geolocation({'latitude':51.5,'longitude':-0.12});pg.click('#cityBtn');pg.click('#loc');pg.wait_for_timeout(1500);ok('location: outside Pakistan rejected','Pakistan only' in pg.inner_text('#toast'),pg.inner_text('#toast'));ctx.close()
    T('location',t3)
    # ---------- 3 alert thresholds ----------
    def scen(name,over,rx,tap=None,neg=False):
        reset();D.update(over);ctx,pg=mk();load(pg)
        if tap:pg.click(f'.rib button:nth-child({tap})');pg.wait_for_timeout(400)
        a=alerts(pg);hit=re.search(rx,a) is not None;ok('alert: '+name,(not hit) if neg else hit,a[:140]);ctx.close();reset()
    T('al1',lambda:scen('heat >= 40°C',dict(hi=[44]*7),'Heat alert'))
    T('al2',lambda:scen('freezing night',dict(lo=[-2]*7),'Freezing'))
    T('al3',lambda:scen('rain chance >= 60%',dict(pp=[70]*7),'70% chance of rain'))
    T('al4',lambda:scen('high UV',dict(uv=[9]*7),'UV index 9'))
    T('al5',lambda:scen('unhealthy air',dict(aqi=180),'Unhealthy air'))
    T('al6',lambda:scen('heavy rain / flood + mountain roads',dict(ps=[60]*7),'Heavy rain.*Mountain roads'))
    T('al7',lambda:scen('strong wind gusts',dict(gust=70),'Strong winds'))
    T('al8',lambda:scen('dust',dict(dust=200),'Dust in the air'))
    T('al9',lambda:scen('fog already over today is NOT shown',dict(vis=lambda i:400 if 5<=i%24<=7 else 20000),'fog',neg=True))
    T('al10',lambda:scen('fog tomorrow morning IS shown',dict(vis=lambda i:400 if 5<=i%24<=7 else 20000),'Dense fog',tap=2))
    T('al11',lambda:scen('fog this evening IS shown',dict(vis=lambda i:400 if 18<=i%24<=20 else 20000),'Dense fog possible around 6:00 PM'))
    def calm():
        reset();ctx,pg=mk();load(pg);ok('alert: calm day shows none',pg.locator('.alerts').count()==0,alerts(pg));ctx.close()
    T('calm',calm)
    # ---------- 4 map / compare ----------
    def t4():
        reset();ctx,pg=mk();load(pg);tool(pg,'map');pg.wait_for_timeout(900);ok('map: 12 cities drawn',pg.locator('#mpP g').count()==12)
        pg.click('[data-m=t]');pg.wait_for_timeout(300);ok('map: temperature mode',pg.inner_text('#mpM').startswith('Hottest'),pg.inner_text('#mpM'))
        pg.click('#mpPl');pg.wait_for_timeout(1300);ok('map: play advances the hours',int(pg.evaluate("document.getElementById('mpS').value"))>0)
        pg.click('#mpPl');pg.locator('#mpP g').nth(3).click(force=True);pg.wait_for_timeout(700);ok('map: tapping a city opens it',pg.inner_text('#hEn').startswith('Karachi'),pg.inner_text('#hEn'))
        tool(pg,'cmp');pg.wait_for_timeout(900);ok('compare: shows Lahore by default and a 7-row table',('Lahore' in pg.inner_text('#cr')) and pg.locator('.cmpt tr').count()==8,pg.inner_text('#cr')[:80])
        pg.select_option('#cb',label='Peshawar');pg.wait_for_timeout(800);ok('compare: changing the city updates',('Peshawar' in pg.inner_text('#cr')))
        ctx.close()
    T('map',t4)
    # ---------- 5 trip ----------
    def t5():
        reset();ctx,pg=mk();load(pg);tool(pg,'trip');pg.wait_for_timeout(900);N=pg.evaluate("ROUTES.map(r=>r[1].length)");bad=[]
        for i,n in enumerate(N):
            pg.select_option('#tr',str(i));pg.wait_for_timeout(700)
            if pg.locator('.stop').count()!=n:bad.append(i)
        ok('trip: all 8 routes list every stop',not bad,bad);close(pg)
        def tc(name,over,day,exp):
            reset();D.update(over);tool(pg,'trip');pg.wait_for_timeout(500);pg.click(f'#td button:nth-child({day})');pg.wait_for_timeout(300)
            h=pg.inner_text('#tx h3');ok('trip: '+name+' -> '+exp,h==exp,h);close(pg);reset()
        tc('clear weather',{},1,'Good to go');tc('rain 70%',dict(pp=[70]*7),1,'Drive with care');tc('heavy rain 60 mm',dict(ps=[60]*7),1,'Avoid if you can')
        tc('snow',dict(code=[71]*7),1,'Drive with care');tc('extreme heat 46°C',dict(hi=[46]*7),1,'Avoid if you can')
        fog=dict(vis=lambda i:400 if 5<=i%24<=7 else 20000);tc('fog already over today',fog,1,'Good to go');tc('fog tomorrow morning',fog,2,'Avoid if you can')
        ctx.close()
    T('trip',t5)
    # ---------- 6 plan ----------
    def t6():
        reset();ctx,pg=mk();load(pg);tool(pg,'plan');ks=pg.evaluate("Object.keys(ACT)");bad=[]
        for k in ks:
            pg.click(f'#pBody [data-k={k}]');pg.wait_for_timeout(250);t=pg.inner_text('#pr')
            if not re.search('[✅⚠️❌]',t) or re.search(BAD,t):bad.append(k)
        ok('plan: all 7 activities give an answer',not bad,bad)
        def ask(q):
            pg.fill('#pq',q);pg.press('#pq','Enter');pg.wait_for_timeout(300);return pg.inner_text('#pr')
        t=ask('Should I go hiking on saturday?');ok('plan: "hiking on saturday" understood',('Sat' in t and 'Hiking' in t),t[:90])
        t=ask('Is tomorrow good for cricket?');ok('plan: "tomorrow cricket" understood',('Tomorrow' in t and 'Cricket' in t),t[:90])
        t=ask('can I dry clothes today');ok('plan: "dry clothes today" understood',('Today' in t and 'clothes' in t.lower()),t[:90])
        t=ask('sunset photos tonight');ok('plan: sunset is not mistaken for Sunday',('Today' in t and 'Photography' in t and 'Sun:' not in t),t[:90])
        pg.click('#pBody [data-k=walk]');pg.wait_for_timeout(250);row=[x for x in pg.locator('#pr .res div').all_inner_texts() if 'Today' in x]
        m=re.search(r'(\d+):\d\d (AM|PM) –',row[0]) if row else None
        st=(int(m.group(1))%12+(12 if m and m.group(2)=='PM' else 0)) if m else None
        ok('plan: today never suggests hours that have already passed (now 2:20 PM)',st is None or st>=14,row)
        close(pg)
        def pc(name,over,k,exp):
            reset();D.update(over);ctx2,p2=mk();load(p2);tool(p2,'plan');p2.click(f'#pBody [data-k={k}]');p2.wait_for_timeout(250)
            p2.fill('#pq','hiking on saturday' if k=='hike' else 'walk tomorrow');p2.press('#pq','Enter');p2.wait_for_timeout(300);t=p2.inner_text('#pr');ok('plan: '+name,exp in t,t[:110]);ctx2.close();reset()
        pc('heavy rain blocks hiking',dict(prob=lambda i:90),'hike','❌');pc('rain reason is explained',dict(prob=lambda i:90),'hike','rain is likely')
        pc('extreme heat blocks a walk',dict(hi=[44]*7,lo=[34]*7),'walk','too hot')
        ctx.close()
    T('plan',t6)
    # ---------- 7 alerts panel + offline + shortcuts ----------
    def t7():
        reset();ctx,pg=mk();load(pg);tool(pg,'alr');ok('alerts panel opens',pg.locator('#at').count()==1);close(pg)
        pg.evaluate("navigator.serviceWorker.ready.then(()=>1)");pg.wait_for_timeout(800);D['off']=True;pg.reload();pg.wait_for_selector('#dial');pg.wait_for_timeout(2500)
        ok('offline: saved forecast banner',"offline" in alerts(pg).lower() and 'saved' in alerts(pg).lower(),alerts(pg)[:90]);D['off']=False;pg.evaluate("dispatchEvent(new Event('online'))");pg.wait_for_timeout(1500);ok('offline: banner clears when back online','offline' not in alerts(pg).lower())
        ctx.close();ctx,pg=mk();load(pg,'/index.html?city=Lahore');ok('shortcut: ?city=Lahore opens Lahore',pg.inner_text('#hEn').startswith('Lahore'),pg.inner_text('#hEn'))
        m=pg.evaluate("fetch('manifest.webmanifest').then(r=>r.json())");ic=[pg.evaluate(f"fetch('{i['src']}').then(r=>r.status)") for i in m['icons']]
        ok('PWA: manifest valid, icons load, 5 shortcuts',m['display']=='standalone' and all(s==200 for s in ic) and len(m['shortcuts'])==5,(m['display'],ic))
        ok('PWA: service worker registers',pg.evaluate("navigator.serviceWorker.ready.then(()=>1)")==1);ctx.close()
    T('pwa',t7)
    # ---------- 8 Urdu coverage ----------
    def t8():
        reset();ctx,pg=mk();load(pg);pg.click('#toolsBtn');pg.click('[data-k=lang]');pg.wait_for_timeout(500);pg.click('#pClose');pg.wait_for_timeout(700)
        js="(()=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),o=new Set();while(w.nextNode()){const n=w.currentNode;if(/SCRIPT|STYLE/.test(n.parentNode.nodeName))continue;(n.nodeValue.match(/[A-Za-z][A-Za-z'’]{2,}/g)||[]).forEach(x=>o.add(x))}return [...o]})()"
        allow=set('AM PM UV AQI mm km mph NW NE SW SE Open Meteo Aasmaan English Peshawar PM2'.split());left=set(pg.evaluate(js))-allow
        for k in ['map','cmp','trip','plan','alr']:
            pg.click('#toolsBtn');pg.click(f'[data-k={k}]');pg.wait_for_timeout(900);left|=set(pg.evaluate(js))-allow;pg.click('#pClose');pg.wait_for_timeout(300)
        city=set(pg.evaluate("CITIES.flatMap(c=>c[0].split(' '))"))|set('Lahore Islamabad Karachi Quetta Multan Faisalabad Rawalpindi Hyderabad Gilgit Skardu Murree Abbottabad Besham Chilas Gujranwala Kallar Kahar Attock Nowshera Jamshoro Khuzdar KKH Lahore'.split());left-=city
        ok('Urdu: no untranslated English words left',not left,sorted(left));ctx.close()
    T('urdu',t8)
    # ---------- 9 small screens ----------
    def t9():
        reset();bad=[]
        for w in (320,360,412):
            ctx,pg=mk(w);load(pg)
            pg.evaluate("window.scrollTo(200,0)")
            if pg.evaluate("document.documentElement.scrollWidth")>w or pg.evaluate("window.scrollX")>0:bad.append(('main',w))
            for k in ['map','cmp','trip','plan','alr']:
                pg.click('#toolsBtn');pg.click(f'[data-k={k}]');pg.wait_for_timeout(700)
                if pg.evaluate("document.getElementById('panel').scrollWidth")>w:bad.append((k,w))
                pg.click('#pClose');pg.wait_for_timeout(250)
            ctx.close()
        ok('layout: nothing overflows at 320/360/412 px wide',not bad,bad)
    T('layout',t9)
    # ---------- 10 sun calculation vs astral ----------
    def t10():
        from astral import LocationInfo
        from astral.sun import sun
        import datetime,zoneinfo
        tz=zoneinfo.ZoneInfo('Asia/Karachi');ctx,pg=mk();load(pg);C=pg.evaluate("CITIES.slice(0,12).map(c=>[c[0],c[2],c[3]])");worst=0
        for n,la,lo in C:
            for (y,m,d) in [(2026,1,15),(2026,4,10),(2026,6,21),(2026,11,1)]:
                a=sun(LocationInfo(n,'PK','Asia/Karachi',la,lo).observer,date=datetime.date(y,m,d),tzinfo=tz)
                ar=a['sunrise'].hour*60+a['sunrise'].minute+a['sunrise'].second/60;as_=a['sunset'].hour*60+a['sunset'].minute+a['sunset'].second/60
                sr,ss=pg.evaluate(f"sunCalc({la},{lo},new Date(Date.UTC({y},{m-1},{d})))");worst=max(worst,abs(sr-ar),abs(ss-as_))
        ok('sun times: app vs independent astronomy library (48 checks), worst error %.1f min'%worst,worst<=3,worst);ctx.close()
    T('sun',t10)
    b.close()
print('\nPASSED %d / %d'%(sum(res),len(res)));print('JS page errors:',errs)
