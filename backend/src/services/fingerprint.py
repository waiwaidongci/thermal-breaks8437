import hashlib,json
VERSIONS={'point':'centered-scaled-exact-dp-v1','duration':'centered-scaled-duration-weighted-exact-dp-v1'}
def fingerprint(batch,points,config,study_mode='point'):
 normalized=[{key:(p[key].isoformat() if hasattr(p[key],'isoformat') else p[key]) for key in ('id','sequence','recorded_at','temperature')} for p in sorted(points,key=lambda x:x['sequence'])]
 payload={'version':VERSIONS[study_mode],'study_mode':study_mode,'batch':batch,'points':normalized,'config':config}
 return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
