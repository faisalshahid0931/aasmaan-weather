const V='aasmaan-v4',SHELL=['./','index.html','manifest.webmanifest','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V&&x!=='aasmaan-city').map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;if(/open-meteo\.com$/.test(new URL(r.url).hostname))return;
e.respondWith(fetch(r).then(res=>{if(res.ok||res.type==='opaque'){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r).then(m=>m||(r.mode==='navigate'?caches.match('index.html'):Response.error()))))});

self.addEventListener('message',e=>{if(e.data&&e.data.type==='city')e.waitUntil(caches.open('aasmaan-city').then(c=>c.put('city',new Response(JSON.stringify(e.data.c)))))});
self.addEventListener('periodicsync',e=>{if(e.tag==='wx')e.waitUntil(chk())});
async function chk(){const m=await(await caches.open('aasmaan-city')).match('city');if(!m)return;const[n,la,lo]=await m.json();
const j=await(await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${la}&longitude=${lo}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,uv_index_max&timezone=Asia%2FKarachi&forecast_days=1`)).json(),d=j.daily,a=[];
if(d.temperature_2m_max[0]>=40)a.push('Heat alert: up to '+Math.round(d.temperature_2m_max[0])+'°C today.');
if(d.precipitation_sum[0]>=50)a.push('Heavy rain expected ('+Math.round(d.precipitation_sum[0])+' mm). Flooding is possible.');else if(d.precipitation_probability_max[0]>=60)a.push(d.precipitation_probability_max[0]+'% chance of rain today.');
if(d.uv_index_max[0]>=8)a.push('Very high UV today.');if(d.temperature_2m_min[0]<=0)a.push('Freezing night ahead.');
if(a.length)await self.registration.showNotification('Aasmaan · '+n,{body:a.join(' '),icon:'icon-192.png',badge:'icon-192.png',tag:'wx-'+new Date().toDateString()})}
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window'}).then(l=>l.length?l[0].focus():clients.openWindow('./')))});
