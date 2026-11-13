from fastapi import HTTPException
from src.models import InspectionNote,SegmentationRun
from src.utils.csv_export import csv_response
from src.services.audit import record

def export_note(db,id,actor):
 note=db.get(InspectionNote,id)
 if not note:raise HTTPException(404,'说明不存在')
 if note.status!='approved':raise HTTPException(409,'仅已确认巡查说明可导出')
 run=db.get(SegmentationRun,note.run_id)
 headers=['巡查说明','运行','输入指纹','段号','起始序号(含)','结束序号(含)','均温','RSS','人工解释','下一步','审核意见','区间起(时刻)','区间止(时刻)','段持续时长(秒)']
 rows=[[note.name,run.name,run.result['fingerprint'],s['position'],s['start']+1,s['end'],s['mean'],s['rss'],note.interpretation,note.next_step,note.review_note,s.get('start_time',''),s.get('end_time',''),s.get('duration_seconds','')] for s in note.segment_snapshot]
 record(db,actor,'note.exported',{'note_id':id});return csv_response(f'thermal-inspection-{id}.csv',rows,headers)
