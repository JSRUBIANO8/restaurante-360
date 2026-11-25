const $ = s => document.querySelector(s);
const money = n => new Intl.NumberFormat('es-CO',{style:'currency',currency:'COP',maximumFractionDigits:0}).format(n);
async function api(path, body, token) {
  const opts = {headers:{'Content-Type':'application/json'}};
  if(body){opts.method='POST';opts.body=JSON.stringify(body)}
  if(token) opts.headers.Authorization='Bearer '+token;
  const r=await fetch(path,opts), data=await r.json();
  if(!r.ok) throw Error(typeof data.detail==='string'?data.detail:'Verifica los datos ingresados');
  return data;
}
function msg(id,text,error=false){const e=$(id);e.textContent=text;e.className=error?'error':'success'}
function values(form){return Object.fromEntries(new FormData(form))}
const reservation=$('#reservation');
const today=new Date();const localDate=new Date(today.getTime()-today.getTimezoneOffset()*60000).toISOString().slice(0,10);
reservation.elements.day.value=localDate;reservation.elements.day.min=localDate;
async function availability(){
  const {day,slot}=values(reservation), select=reservation.elements.table_id;
  select.replaceChildren();
  try{const d=await api('/api/availability?'+new URLSearchParams({day,slot}));
  for(const n of d.available)select.add(new Option('Mesa '+n,n));
  msg('#reservation-msg',d.available.length?`${d.available.length} mesas disponibles`:'No hay mesas disponibles',!d.available.length)}catch(e){msg('#reservation-msg',e.message,true)}
}
$('#availability').onclick=availability;reservation.elements.day.onchange=availability;reservation.elements.slot.onchange=availability;
reservation.onsubmit=async e=>{e.preventDefault();const d=values(reservation);d.table_id=Number(d.table_id);d.guests=Number(d.guests);try{const r=await api('/api/reservations',d);await availability();msg('#reservation-msg','Reserva confirmada: '+r.confirmation)}catch(e){msg('#reservation-msg',e.message,true)}};
$('#order').onsubmit=async e=>{e.preventDefault();const d=values(e.target);d.quantity=Number(d.quantity);try{const r=await api('/api/orders',d);msg('#order-msg',r.confirmation+' · Total: '+money(r.total))}catch(e){msg('#order-msg',e.message,true)}};
$('#login').onsubmit=async e=>{e.preventDefault();$('#metrics').replaceChildren();try{const {token}=await api('/api/login',values(e.target));e.target.reset();const r=await api('/api/reports',null,token);for(const [label,value] of [['Reservas',r.reservations],['Pedidos',r.orders],['Ventas registradas',money(r.revenue)]]){const div=document.createElement('div');div.className='metric';const strong=document.createElement('strong');strong.textContent=value;div.append(strong,document.createTextNode(label));$('#metrics').append(div)}msg('#login-msg','Indicadores actualizados')}catch(e){msg('#login-msg',e.message,true)}};
async function init(){try{const menu=await api('/api/menu');for(const [name,price] of Object.entries(menu)){const row=document.createElement('div');row.className='menu-row';const a=document.createElement('span'),b=document.createElement('strong');a.textContent=name;b.textContent=money(price);row.append(a,b);$('#menu').append(row);$('#order').elements.item.add(new Option(name,name))}}catch(e){msg('#order-msg',e.message,true)}await availability()}
init();
