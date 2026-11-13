export const number=(v:number,d=3)=>Number.isFinite(v)?v.toLocaleString('zh-CN',{maximumFractionDigits:d}):'—';
export const date=(v:string)=>new Date(v).toLocaleString('zh-CN',{hour12:false});
export const duration=(s:number)=>{
 if(!Number.isFinite(s))return '—';
 const h=Math.floor(s/3600),m=Math.floor(s%3600/60),sec=Math.round(s%60);
 const parts:string[]=[];
 if(h)parts.push(h+' 时');
 if(m)parts.push(m+' 分');
 if(!h&&!m)return number(s,1)+' 秒';
 if(sec)parts.push(sec+' 秒');
 return parts.join(' ')||'0 秒';
};
// datetime-local input works in browser time; helpers convert to/from timezone-aware ISO strings.
export const toLocalInput=(iso:string)=>{
 const d=new Date(iso),pad=(x:number)=>String(x).padStart(2,'0');
 return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};
