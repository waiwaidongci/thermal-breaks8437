import type {Run} from '../types/domain';
import {Badge} from './common/Badge';
import {Table} from './common/Table';
export function RunTable({runs,select}:{runs:Run[];select:(r:Run)=>void}){
 return <Table headers={['归档运行','状态','研究口径 / 段约束','罚项 β','结果']}>
  {runs.map(r=>{
   const durationMode=r.result?.study_mode==='duration'||r.config?.study_mode==='duration';
   return <tr key={r.id}>
    <td><strong>{r.name}</strong><small>#{r.id}</small></td>
    <td><Badge status={r.status}/>{r.error&&<small className="fire">{r.error}</small>}</td>
    <td>{durationMode?`按时长 / ${r.config.min_duration} 秒`:`按点数 / ${r.config.min_size} 点`}<small>段数上界 {r.config.max_segments}</small></td>
    <td>{r.config.penalty}</td>
    <td><button onClick={()=>select(r)}>打开研究 ↗</button></td>
   </tr>;})}
 </Table>;
}
