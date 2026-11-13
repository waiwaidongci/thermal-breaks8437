import {PageTitle} from '../components/common/PageTitle';
import {Empty} from '../components/common/Empty';
import {Badge} from '../components/common/Badge';
import {ThermalChart} from '../components/ThermalChart';
import {RunSummary} from '../components/RunSummary';
import {PenaltyPath} from '../components/PenaltyPath';
import {SegmentTable} from '../components/SegmentTable';
import {number,date,duration} from '../utils/format';

export function ResultsPage({runs,selectedId,select}:any){
 const run=runs.find((r:any)=>r.id===selectedId)||runs[0],result=run?.result,isDuration=result?.study_mode==='duration';
 const first=result?.segments?.[0],last=result?.segments?.[result.segments.length-1];
 const accounted=result?result.segments.reduce((acc:number,s:any)=>acc+(s.duration_seconds||0),0):0; return <>
  <PageTitle index="04" title="把断点放回整段热程。" description={isDuration?'断点 b = 左侧累计样本数；区间从样本 b 时刻起，到下一段起点时刻止，末段止于研究结束时刻。':'断点 b = 左侧累计样本数；样本 b 仍在左段，b+1 开始右段。'}/>
  <label>归档运行<select value={run?.id||''} onChange={e=>select(runs.find((r:any)=>r.id===+e.target.value))}>{runs.map((r:any)=><option key={r.id} value={r.id}>#{r.id} {r.name}</option>)}</select></label>
  {run&&<p><Badge status={run.status}/>　{run.error}</p>}
  {!result
   ?<Empty title={run?.status==='failed'?'本次分段未完成':'等待真实 worker 求解'} help={run?.error||'短任务每3秒刷新；请先在配置页建立运行。'}/>
   :<>
    <RunSummary result={result}/>
    {isDuration&&<div className="interpretation">
     <strong>区间起止与总时长核对</strong>
     <p>窗口 {date(first.start_time)} → {date(result.end_time)}；最短段长 {number(result.min_duration,1)} 秒。各段时长合计 {duration(accounted)}（{number(accounted,1)} 秒），研究窗口总时长 {duration(result.total_duration_seconds)}（{number(result.total_duration_seconds,1)} 秒），{Math.abs(accounted-result.total_duration_seconds)<1e-6?'两者一致 ✓':'两者不一致，请核对输入'}</p>
     <p>末段止点 {date(last.end_time)} 必须等于研究结束时刻；段与段首尾相接、不重不漏。</p>
    </div>}
    <ThermalChart series={result.series} segments={result.segments}/>
    <div className="interpretation"><strong>断点是离线近似的切分位置。</strong><p>平滑漂移也可能被表示为多段常值；相邻均值差不是置信区间、显著性检验或工艺原因。巡查前请核对采样和仪器记录。</p></div>
    <SegmentTable result={result}/>
    <PenaltyPath result={result}/>
    <details className="provenance">
     <summary>冻结输入指纹、精度与规则</summary>
     <p className="fingerprint">{result.fingerprint}</p>
     <p>origin={result.numeric_stability.origin} / scale={result.numeric_stability.scale} / {result.numeric_stability.prefix_precision}</p>
     <p>{result.tie_rule}</p>
     <p>目标 RSS + β(K−1)，预设上界 {result.requested_max_segments}，实际可行上界 {result.feasible_max_segments}。</p>
     {isDuration&&<p>{result.duration_definition}；{result.segment_length_rule}。{result.boundary_definition}</p>}
    </details>
    <a className="text-link" href="#notes">形成可审阅的巡查说明 →</a>
   </>}
 </>;
}
