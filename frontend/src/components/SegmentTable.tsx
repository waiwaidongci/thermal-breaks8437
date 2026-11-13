import {number,date,duration} from '../utils/format';
import {Table} from './common/Table';
export function SegmentTable({result}:{result:any}){
 const isDuration=result.study_mode==='duration';
 return <section className="section">
  <div className="section-heading">
   <h2>分段与相邻均值差</h2>
   <span>{isDuration?'区间 [起点时刻, 止点时刻)，末段止于研究结束时刻':'数组 [start,end) / 页面序号 start+1…end'}</span>
  </div>
  <Table headers={isDuration
   ?['段号','起始—结束（均含）','点数','区间起（时刻）','区间止（时刻）','持续时长','均温 °C','RSS（°C²·秒）','与前段均值差']
   :['段号','起始—结束（均含）','点数','均温 °C','RSS','与前段均值差']}>
   {result.segments.map((s:any,i:number)=>
    <tr key={s.position}>
     <td><strong>0{s.position}</strong></td>
     <td>{s.start+1} — {s.end}</td>
     <td>{s.count}</td>
     {isDuration&&<>
      <td><small>{date(s.start_time)}</small></td>
      <td><small>{date(s.end_time)}</small></td>
      <td>{duration(s.duration_seconds)}<small>{number(s.duration_seconds,1)} 秒</small></td>
     </>}
     <td>{number(s.mean,5)}</td>
     <td>{number(s.rss,5)}</td>
     <td>{i?number(result.adjacent_mean_differences[i-1].difference,5):'—'}</td>
    </tr>)}
  </Table>
  {isDuration&&<p>各段持续时长合计 {duration(result.total_duration_seconds)}（{number(result.total_duration_seconds,1)} 秒），应与研究窗口总时长一致。</p>}
 </section>;
}
