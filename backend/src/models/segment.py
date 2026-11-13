from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import ForeignKey,Float,String,UniqueConstraint
from src.config.database import Base
class Segment(Base):
 __tablename__='segments'
 __table_args__=(UniqueConstraint('run_id','position'),)
 id:Mapped[int]=mapped_column(primary_key=True)
 run_id:Mapped[int]=mapped_column(ForeignKey('segmentation_runs.id'))
 position:Mapped[int]=mapped_column()
 start:Mapped[int]=mapped_column()
 end:Mapped[int]=mapped_column()
 mean:Mapped[float]=mapped_column(Float)
 rss:Mapped[float]=mapped_column(Float)
 # Duration-study columns only; null for historical point-count runs.
 duration_seconds:Mapped[float|None]=mapped_column(Float,nullable=True)
 start_time:Mapped[str|None]=mapped_column(String(40),nullable=True)
 end_time:Mapped[str|None]=mapped_column(String(40),nullable=True)
