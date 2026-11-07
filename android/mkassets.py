# Builds assets/index.html (the Android-wrapped copy) from the web app: bundles fonts, wires the native bridge.
import re,sys
src=sys.argv[1] if len(sys.argv)>1 else '../web/index.html'
s=open(src,encoding='utf8').read()
def r(o,n):
    global s
    assert o in s,o[:80]
    s=s.replace(o,n,1)
s=re.sub(r'<link rel="preconnect" href="https://fonts.googleapis.com">\s*<link href="https://fonts.googleapis.com/[^>]*>','@@FONTS@@',s,count=1)
F=""
for fam,w,f in [('Fraunces',300,'fraunces-latin-300'),('Fraunces',600,'fraunces-latin-600'),('Manrope',400,'manrope-latin-400'),('Manrope',600,'manrope-latin-600'),('Manrope',800,'manrope-latin-800'),('Noto Nastaliq Urdu',400,'noto-nastaliq-urdu-arabic-400'),('Noto Nastaliq Urdu',600,'noto-nastaliq-urdu-arabic-600'),('Noto Naskh Arabic',400,'noto-naskh-arabic-arabic-400'),('Noto Naskh Arabic',600,'noto-naskh-arabic-arabic-700'),('Noto Naskh Arabic',700,'noto-naskh-arabic-arabic-700')]:
    F+=f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;src:url(fonts/{f}-normal.woff2) format('woff2')}}"
assert '@@FONTS@@' in s
s=s.replace('@@FONTS@@','<style>'+F+'</style>')
r("if('serviceWorker'in navigator&&/^https?:/.test(location.protocol))","if('serviceWorker'in navigator&&!window.AasmaanApp&&/^https?:/.test(location.protocol))")
r("try{if(navigator.share)await navigator.share(","if(window.AasmaanApp){AasmaanApp.share(t);return}try{if(navigator.share)await navigator.share(")
r("const alOn=()=>{try{return localStorage.getItem('al')==='1'&&'Notification'in window&&Notification.permission==='granted'}catch(e){return 0}};","const NA=window.AasmaanApp;const alOn=()=>{try{return localStorage.getItem('al')==='1'&&(NA?NA.canNotify():'Notification'in window&&Notification.permission==='granted')}catch(e){return 0}};")
r("async function syncAlerts(){try{","async function syncAlerts(){if(NA)return;try{")
r("navigator.serviceWorker.ready.then(r=>r.showNotification('Aasmaan · '+CITIES[S.city][0],{body:S.al.join(' '),icon:'icon-192.png',badge:'icon-192.png',tag:'wx'})).catch(()=>{});","if(NA)NA.notify('Aasmaan · '+CITIES[S.city][0],S.al.join(' '));else navigator.serviceWorker.ready.then(r=>r.showNotification('Aasmaan · '+CITIES[S.city][0],{body:S.al.join(' '),icon:'icon-192.png',badge:'icon-192.png',tag:'wx'})).catch(()=>{});")
m=re.search(r"if\(!\('Notification'in window\)\)(return toast\(u\('Notifications are not supported here','[^']*'\)\));\s*const p=await Notification\.requestPermission\(\);if\(p!=='granted'\)",s)
assert m
s=s.replace(m.group(0),"let p='granted';if(NA){NA.askNotify();for(let i=0;i<40&&!NA.canNotify();i++)await new Promise(r=>setTimeout(r,500));if(!NA.canNotify())p='denied'}else{if(!('Notification'in window))"+m.group(1)+";p=await Notification.requestPermission()}if(p!=='granted')",1)
a=s.index("Alerts are checked when");b=s.index("only support checks while the app is open.")+len("only support checks while the app is open.")
s=s[:a]+"Alerts are checked each time you open the app. Background alerts are not available yet."+s[b:]
c=s.index("ایپ کھولنے پر الرٹس چیک ہوتے ہیں۔");d=s.index("چیک کرتے ہیں۔",c)+len("چیک کرتے ہیں۔")
s=s[:c]+"ایپ کھولنے پر ہر بار الرٹس چیک ہوتے ہیں۔ بیک گراؤنڈ الرٹس ابھی دستیاب نہیں۔"+s[d:]
open('assets/index.html','w',encoding='utf8').write(s);print('assets/index.html written',len(s))
