from datetime import datetime,timezone
from .validation import validate_points,validate_config,validate_duration_config
from .costs import StableCosts
from .duration import WeightedCosts,duration_weights,build_duration_frontier
from .dynamic_program import build_frontier
from .penalty_path import select_partition,evaluate_path
from .fingerprint import fingerprint

def _duration_inputs(points,config):
 end=validate_duration_config(config)
 times=[p['recorded_at'] if isinstance(p['recorded_at'],datetime) else datetime.fromisoformat(p['recorded_at'].replace('Z','+00:00')) for p in points]
 for t in times:
  if t.tzinfo is None or t.utcoffset() is None:raise ValueError('时间必须包含时区')
 times=[t.astimezone(timezone.utc) for t in times]
 if end<=times[-1]:raise ValueError('结束时刻必须晚于最后一个观测时刻')
 weights=duration_weights(times,end)
 return times,end,weights

def _annotate_times(segments,times,end):
 for s in segments:
  s['start_time']=times[s['start']].isoformat();s['end_time']=(times[s['end']] if s['end']<len(times) else end).isoformat()
 return segments

def analyze(batch,points,config):
 points=validate_points(points);study_mode=config.get('study_mode','point')
 if study_mode=='duration':
  times,end,weights=_duration_inputs(points,config)
  config={**config,'end_time':end.isoformat()}  # normalize so fingerprint/JSON never receive a raw datetime
  costs=WeightedCosts([p['temperature'] for p in points],weights)
  frontier=build_duration_frontier(costs,config['min_duration'],config['max_segments'])
  feasible=frontier['feasible_max_segments']
  selected=select_partition(frontier,costs,config['penalty'])
  _annotate_times(selected['segments'],times,end)
  path=evaluate_path(frontier,costs,config['penalties']+[config['penalty']])
  for entry in path:_annotate_times(entry['segments'],times,end)
  mode_meta={'study_mode':'duration','end_time':end.isoformat(),'min_duration':config['min_duration'],'total_duration_seconds':float(costs.sw[len(points)]),'duration_definition':'zero-order hold: each temperature lasts until the next sample; the last sample lasts until end_time','segment_length_rule':'each segment duration must be >= min_duration seconds','boundary_definition':'breakpoint b is left sample count; the segment runs from the timestamp of sample a+1 up to (but not including) the timestamp of sample b+1; the last segment ends at end_time'}
  fp_config={k:v for k,v in config.items() if k!='study_mode'}
 else:
  feasible=validate_config(config,len(points));costs=StableCosts([p['temperature'] for p in points]);frontier=build_frontier(costs,config['min_size'],config['max_segments']);selected=select_partition(frontier,costs,config['penalty']);path=evaluate_path(frontier,costs,config['penalties']+[config['penalty']])
  mode_meta={'study_mode':'point'}
  fp_config={k:v for k,v in config.items() if k not in ('study_mode','end_time','min_duration')}
 return {**selected,**mode_meta,'n':len(points),'feasible_max_segments':feasible,'requested_max_segments':config['max_segments'],'min_size':config['min_size'] if study_mode=='point' else None,'fingerprint':fingerprint(batch,points,fp_config,study_mode),'series':[{'sequence':p['sequence'],'recorded_at':p['recorded_at'].isoformat() if hasattr(p['recorded_at'],'isoformat') else p['recorded_at'],'temperature':p['temperature']} for p in points],'penalty_path':path,'rss_frontier':[{'segments_count':k,'optimal_rss':float(frontier['dp'][k,len(points)]*costs.scale*costs.scale)} for k in range(1,feasible+1)],'dp_builds':1,'numeric_stability':{'origin':float(costs.origin),'scale':float(costs.scale),'prefix_precision':'numpy.longdouble centered/scaled cumulative duration-weighted moments' if study_mode=='duration' else 'numpy.longdouble centered/scaled cumulative moments'},'tie_rule':'equal objective prefers fewer segments within relative longdouble tolerance; fixed-K uses earliest prior cut within relative longdouble roundoff tolerance (earliest last cut, recursively)','interpretation':'Offline piecewise-constant mean approximation. Penalty path is sensitivity, not a confidence interval, online alarm, or causal attribution. Smooth drift can be approximated as steps; independent equal-variance segment errors are a working approximation.'}
