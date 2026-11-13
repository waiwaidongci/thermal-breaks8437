import {useState,useEffect} from 'react';
import {researchApi} from '../api/research';
import {useAsync} from '../hooks/useAsync';
import {PageTitle} from '../components/common/PageTitle';
import {RunTable} from '../components/RunTable';
import {Notice} from '../components/common/Notice';
import {toLocalInput} from '../utils/format';

export function ConfigPage({batches,points,runs,user,reload,select}:any){
 const [batch,B]=useState(0);
 const [name,N]=useState('离线热程研究 '+new Date().toLocaleTimeString());
 const [mode,setMode]=useState<'point'|'duration'>('point');
 const [min,M]=useState(12);
 const [minDuration,setMinDuration]=useState(60);
 const [max,K]=useState(8);
 const [penalty,P]=useState(80);
 const [path,Q]=useState('0,20,80,320,1280');
 const [endText,setEndText]=useState('');
 const state=useAsync();
 const id=batch||batches[0]?.id;
 const list=points.filter((p:any)=>p.batch_id===id);
 const n=list.length;
 const lastAt=list.length?list[list.length-1].recorded_at:'';
 const firstAt=list.length?list[0].recorded_at:'';
 // Default the end time to one 30s step after the last sample whenever the batch changes.
 useEffect(()=>{
  if(lastAt)setEndText(toLocalInput(new Date(new Date(lastAt).getTime()+30000).toISOString()));
 },[lastAt]);
 const effectiveEnd=endText?new Date(endText):null;
 const endParsed=effectiveEnd&&!Number.isNaN(effectiveEnd.getTime());
 const totalWindow=list.length&&endParsed?(effectiveEnd!.getTime()-new Date(firstAt).getTime())/1000:0;
 const feasibleByDuration=minDuration>0&&totalWindow>0?Math.floor(totalWindow/minDuration):0;
 const endInvalid=!endText||!endParsed||!!lastAt&&effectiveEnd!.getTime()<=new Date(lastAt).getTime();
 const durationBlocked=mode==='duration'&&(endInvalid||!minDuration||minDuration<=0||feasibleByDuration<1);
 const submit=async(e:React.FormEvent)=>{
  e.preventDefault();
  await state.act(async()=>{
   const payload:any=mode==='point'
    ?{batch_id:id,name,study_mode:'point',min_size:min,max_segments:max,penalty,penalties:path.split(',').map(Number)}
    :{batch_id:id,name,study_mode:'duration',max_segments:max,penalty,penalties:path.split(',').map(Number),min_duration:minDuration,end_time:effectiveEnd!.toISOString()};
   const r=await researchApi.createRun(payload);
   await reload();select(r);
  },'已进入真实计算队列');
 };
 return <>
  <PageTitle index="03" title="先定代价，再寻找分段。" description="精确 DP 保存各 K 最优 RSS；多个预设罚项复用同一 frontier。"/>
  <div className="config-split">
   <form className="input-sheet" onSubmit={submit}>
    <label>温度批次
     <select value={id||''} onChange={e=>B(+e.target.value)}>{batches.map((b:any)=><option key={b.id} value={b.id}>{b.name}</option>)}</select>
    </label>
    <label>研究名称<input required value={name} onChange={e=>N(e.target.value)}/></label>
    <label>研究口径
     <select value={mode} onChange={e=>setMode(e.target.value as 'point'|'duration')}>
      <option value="point">按点数（历史口径，每点等权）</option>
      <option value="duration">按持续时间（零阶保持，时长加权）</option>
     </select>
    </label>
    {mode==='point'
     ?<div className="field-pair">
      <label>最小段长 min_size（点）<input type="number" min={1} max={600} value={min} onChange={e=>M(+e.target.value)} required/></label>
      <label>段数上界 max_segments<input type="number" min={1} max={12} value={max} onChange={e=>K(+e.target.value)} required/></label>
     </div>
     :<div className="field-pair">
      <label>最短持续时长 min_duration（秒）<input type="number" min={0} step="any" value={minDuration} onChange={e=>setMinDuration(+e.target.value)} required/></label>
      <label>段数上界 max_segments<input type="number" min={1} max={12} value={max} onChange={e=>K(+e.target.value)} required/></label>
     </div>}
    {mode==='duration'&&<>
     <label>研究结束时刻（末点持续至此时刻）
      <input type="datetime-local" step="1" required value={endText} onChange={e=>setEndText(e.target.value)}/>
      <small style={{color:'var(--muted)'}}>输入按浏览器时区解释，提交带时区 ISO 时间；须严格晚于最后观测 {lastAt?new Date(lastAt).toLocaleString('zh-CN',{hour12:false}):'—'}</small>
     </label>
     {endInvalid&&<p style={{color:'var(--fire)'}}>结束时刻无效或不晚于最后观测时刻，后端将拒绝研究。</p>}
     <p>研究窗口总时长 {totalWindow.toLocaleString('zh-CN',{maximumFractionDigits:1})} 秒，按最短段长可行段数上界 min({max}, floor({totalWindow.toLocaleString('zh-CN',{maximumFractionDigits:1})}/{minDuration}))={Math.min(max,feasibleByDuration)}。总时长不足一个最短段时无法建立研究。</p>
    </>}
    {mode==='point'&&<p>N={n}，可行段数上界 min({max}, floor({n}/{min}))={Math.min(max,Math.floor(n/min))}。max_segments 是上界，不要求达到。</p>}
    <label>当前罚项 β<input type="number" min={0} max={1000000000000} step="any" value={penalty} onChange={e=>P(+e.target.value)} required/></label>
    <label>预设罚项路径（逗号分隔，至少2项）<input value={path} onChange={e=>Q(e.target.value)} required/></label>
    {user.role!=='viewer'
     ?<button className="primary" disabled={state.busy||durationBlocked}>送入分段队列 →</button>
     :<p>观察员只能阅读已有运行。</p>}
    <Notice {...state}/>
   </form>
   <aside className="margin-note">
    <small>OBJECTIVE / DEFINITIONS</small>
    {mode==='point'
     ?<><h2>Σ RSS<br/>+ β · (K − 1)</h2>
      <p>每个观测等权。第一段不受罚。目标相同取更少段；固定 K 的数值相同最优路径取更早的最后切点，递归遵循相同规则。</p>
      <p>温度先中心化并稳定缩放，再累计一、二阶矩。恒温合法，β=0 时也保留一段。</p></>
     :<><h2>Σ wᵢ·(yᵢ−ȳ)²<br/>+ β · (K − 1)</h2>
      <p>每点温度持续到下一点，末点持续到指定结束时刻；wᵢ 为该点持续秒数。均温、RSS 与总目标均按时长加权，段约束为最短持续时长。β 与 RSS 同量纲（°C²·秒），不与按点数研究的 β 数值通用。</p>
      <p>同温区间内加密测点只切分持续时长，不改变区间均温、RSS 与断点时刻。结束时刻无效或总时长无法满足最短段时拒绝研究。</p></>}
    <p>独立、同方差片段误差只是工作近似；这里没有因果归因或在线告警。</p>
   </aside>
  </div>
  <section className="section">
   <h2>运行状态</h2>
   <RunTable runs={runs} select={select}/>
  </section>
 </>;
}
