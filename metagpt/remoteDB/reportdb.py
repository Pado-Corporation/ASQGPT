from . import DBBASE
from sqlalchemy import Column, String, Integer, JSON


class DBReport(DBBASE):
    __tablename__ = "reports"
    report_id = Column(Integer, autoincrement=True, primary_key=True)
    topic = Column(String)
    links = Column(JSON)
    queries = Column(JSON)
    summaries = Column(JSON)
    content = Column(String)
    write_by = Column(String)
    report_type = Column(String)
