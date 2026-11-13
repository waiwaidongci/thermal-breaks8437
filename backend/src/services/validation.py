import math
from datetime import datetime,timezone

def validate_points(points):
 if not 1<=len(points)<=600:raise ValueError('每批必须1..600点')
 ordered=sorted(points,key=lambda p:p['sequence'])
 if [p['sequence'] for p in ordered]!=list(range(1,len(ordered)+1)):raise ValueError('序号须从1连续且唯一')
 times=[]
 for p in ordered:
  if not math.isfinite(p['temperature']) or abs(p['temperature'])>1e12:raise ValueError('温度必须有限且绝对值不超1e12')
  t=p['recorded_at'];t=datetime.fromisoformat(t.replace('Z','+00:00')) if isinstance(t,str) else t
  if t.tzinfo is None or t.utcoffset() is None:raise ValueError('时间必须包含时区')
  times.append(t.astimezone(timezone.utc))
 if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('时间必须按序号严格递增，不能重复或倒序')
 for p,t in zip(ordered,times):p['recorded_at']=t
 return ordered

def validate_config(config,n):
 m=config['min_size'];k=config['max_segments'];b=config['penalty'];path=config['penalties']
 if not isinstance(m,int) or isinstance(m,bool) or not 1<=m<=600 or m>n:raise ValueError('min_size超出样本数或合法范围')
 if not isinstance(k,int) or isinstance(k,bool) or not 1<=k<=12:raise ValueError('max_segments必须1..12')
 if not math.isfinite(b) or not 0<=b<=1e12 or not 2<=len(path)<=12 or any(not math.isfinite(x) or not 0<=x<=1e12 for x in path):raise ValueError('罚项需有限非负且路径2..12项')
 if len(set(path))<2:raise ValueError('罚项路径至少两个不同值')
 return min(k,n//m)

def validate_duration_config(config,points=None):
 m=config['min_duration'];k=config['max_segments'];b=config['penalty'];path=config['penalties'];end=config['end_time']
 if not isinstance(m,(int,float)) or isinstance(m,bool) or not math.isfinite(m) or m<=0 or m>1e12:raise ValueError('min_duration须为正数（秒）')
 if not isinstance(k,int) or isinstance(k,bool) or not 1<=k<=12:raise ValueError('max_segments必须1..12')
 if not math.isfinite(b) or not 0<=b<=1e12 or not 2<=len(path)<=12 or any(not math.isfinite(x) or not 0<=x<=1e12 for x in path):raise ValueError('罚项需有限非负且路径2..12项')
 if len(set(path))<2:raise ValueError('罚项路径至少两个不同值')
 if isinstance(end,str):end=datetime.fromisoformat(end.replace('Z','+00:00'))
 if not isinstance(end,datetime) or end.tzinfo is None or end.utcoffset() is None:raise ValueError('结束时刻必须是带时区的有效时间')
 end=end.astimezone(timezone.utc)
 if points is not None:
  times=[p['recorded_at'] if isinstance(p['recorded_at'],datetime) else datetime.fromisoformat(p['recorded_at'].replace('Z','+00:00')) for p in points]
  times=[t.astimezone(timezone.utc) for t in times]
  if end<=times[-1]:raise ValueError('结束时刻必须晚于最后一个观测时刻')
  total=(end-times[0]).total_seconds()
  if total<m:raise ValueError(f'最短段长无法满足：研究窗口总时长 {total:g} 秒小于最短段长 {m:g} 秒')
 return end
