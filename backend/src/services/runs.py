from sqlalchemy import select
from fastapi import HTTPException
from src.models import SegmentationRun
from src.utils.serialize import row
from .batches import batch_data
from .validation import validate_points,validate_config,validate_duration_config
from .audit import record

def create_run(db,data,actor):
 _,points=batch_data(db,data.batch_id)
 payload=data.model_dump(exclude={'batch_id','name'})
 if payload['study_mode']=='duration':
  if payload['end_time'] is None or payload['min_duration'] is None:raise HTTPException(422,'按时长研究必须提供结束时刻与最短持续时长')
  config={k:v for k,v in payload.items() if v is not None}
  # JSON-safe: store the configured end time as an ISO string, points are revalidated by the worker.
  config['end_time']=config['end_time'].isoformat()
  try:
   validate_points(points);validate_duration_config(config,points)
  except ValueError as e:raise HTTPException(422,str(e))
 else:
  # Point mode keeps the historical config shape exactly: no new keys, fingerprints stay unchanged.
  if payload['min_size'] is None:raise HTTPException(422,'按点数研究必须提供 min_size')
  config={k:payload[k] for k in ('min_size','max_segments','penalty','penalties')}
  try:validate_config(config,len(points))
  except ValueError as e:raise HTTPException(422,str(e))
 if db.scalar(select(SegmentationRun).where(SegmentationRun.name==data.name)):raise HTTPException(409,'运行名称已存在')
 run=SegmentationRun(batch_id=data.batch_id,name=data.name,config=config,created_by=actor,status='queued');db.add(run);db.commit()
 try:
  from src.worker import analyze_run
  analyze_run.delay(run.id)
 except Exception:
  run.status='failed';run.error='队列不可用，请稍后重试';db.commit();raise HTTPException(503,run.error)
 record(db,actor,'run.queued',{'run_id':run.id,'study_mode':config.get('study_mode','point')});return row(run)
