from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
from typing import Literal
class RunInput(BaseModel):
 model_config=ConfigDict(allow_inf_nan=False)
 batch_id:int=Field(gt=0)
 name:str=Field(min_length=2,max_length=180)
 study_mode:Literal['point','duration']='point'
 min_size:int|None=Field(default=None,ge=1,le=600,strict=True)
 max_segments:int=Field(ge=1,le=12,strict=True)
 penalty:float=Field(ge=0,le=1e12)
 penalties:list[float]=Field(min_length=2,max_length=12)
 end_time:datetime|None=None
 min_duration:float|None=Field(default=None,gt=0,le=1e12)
