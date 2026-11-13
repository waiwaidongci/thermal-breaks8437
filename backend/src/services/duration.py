import numpy as np

def duration_weights(times,end_time):
 # Zero-order hold: point i lasts until point i+1; the last point lasts until end_time.
 gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:])]
 gaps.append((end_time-times[-1]).total_seconds())
 weights=np.array(gaps,dtype=np.longdouble)
 if not np.isfinite(weights).all() or (weights<=0).any():raise ValueError('每点持续时长须为正且有限')
 return weights

class WeightedCosts:
 # Duration-weighted first/second moments, same centering/scaling stability scheme as StableCosts.
 def __init__(self,values,weights):
  self.y=np.asarray(values,dtype=np.longdouble);self.w=np.asarray(weights,dtype=np.longdouble)
  if self.y.ndim!=1 or not 1<=len(self.y)<=600 or not np.isfinite(self.y).all() or (np.abs(self.y)>1e12).any():raise ValueError('序列须有限，一维，1..600点，温度绝对值≤1e12')
  if self.w.shape!=self.y.shape or not np.isfinite(self.w).all() or (self.w<=0).any():raise ValueError('每点持续时长须为正且有限')
  self.origin=self.y[0];spread=np.max(np.abs(self.y-self.origin));self.scale=spread if spread else np.longdouble(1)
  z=(self.y-self.origin)/self.scale
  self.sw=np.r_[np.longdouble(0),np.cumsum(self.w,dtype=np.longdouble)]
  self.s=np.r_[np.longdouble(0),np.cumsum(self.w*z,dtype=np.longdouble)]
  self.q=np.r_[np.longdouble(0),np.cumsum(self.w*z*z,dtype=np.longdouble)]
 def duration(self,starts,end):
  return self.sw[end]-self.sw[np.asarray(starts,dtype=int)]
 def normalized(self,starts,end):
  starts=np.asarray(starts,dtype=int);w=self.duration(starts,end)
  v=(self.q[end]-self.q[starts])-(self.s[end]-self.s[starts])**2/w
  return np.maximum(v,np.longdouble(0))
 def segment(self,start,end):
  w=self.sw[end]-self.sw[start];mean=self.origin+self.scale*(self.s[end]-self.s[start])/w
  return {'start':int(start),'end':int(end),'count':int(end-start),'duration_seconds':float(w),'mean':float(mean),'rss':float(self.normalized([start],end)[0]*self.scale*self.scale)}

def build_duration_frontier(costs,min_duration,max_segments):
 n=len(costs.y);total=float(costs.sw[n]);bound=min(max_segments,int(total//np.longdouble(min_duration)))
 if bound<1:raise ValueError('最短段长无法满足：总时长不足一个最短段')
 limit=np.longdouble(min_duration)
 dp=np.full((max_segments+1,n+1),np.longdouble(np.inf));prev=np.full((max_segments+1,n+1),-1,dtype=int);dp[0,0]=0
 achievable=1  # K=1 always reachable; discrete cuts may make higher K in the floor-based bound unreachable.
 for k in range(1,max_segments+1):
  if k>bound:break
  for end in range(k,n+1):
   starts=np.arange(0,end)
   reachable=np.isfinite(dp[k-1,starts]);length_ok=costs.duration(starts,end)>=limit;mask=reachable&length_ok
   if not mask.any():continue
   starts=starts[mask];candidate=dp[k-1,starts]+costs.normalized(starts,end)
   # Relative longdouble roundoff ties prefer earliest prior cut, recursively (same rule as point DP).
   best=np.min(candidate);finite=np.isfinite(candidate)
   tolerance=np.finfo(np.longdouble).eps*64*np.maximum(np.abs(candidate[finite]),max(abs(best),np.finfo(np.longdouble).tiny))
   eligible=np.flatnonzero(finite)[candidate[finite]<=best+tolerance]
   index=int(eligible[0]);dp[k,end]=candidate[index];prev[k,end]=starts[index]
  if np.isfinite(dp[k,n]):achievable=k
 return {'dp':dp[:achievable+1,:],'previous':prev[:achievable+1,:],'feasible_max_segments':achievable,'n':n}
