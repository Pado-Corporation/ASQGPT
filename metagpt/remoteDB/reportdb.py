from . import DBBASE, SESSION
from sqlalchemy import Column, String, Integer, JSON


class DBReport(DBBASE):
    __tablename__ = "test_reports"
    workflow_id = Column(Integer)
    report_id = Column(Integer, autoincrement=True, primary_key=True)
    topic = Column(String)
    links = Column(JSON)
    queries = Column(JSON)
    summaries = Column(JSON)
    content = Column(String)
    write_by = Column(String)
    report_type = Column(String)


from sqlalchemy import or_, and_


# 데이터 삽입 (Create)
def add_report(topic, links, queries, summaries, content, write_by, report_type):
    new_report = DBReport(
        topic=topic,
        links=links,
        queries=queries,
        summaries=summaries,
        content=content,
        write_by=write_by,
        report_type=report_type,
    )
    SESSION.add(new_report)
    SESSION.commit()


# 데이터 검색 (Read)


def get_reports_by_topic(topic):
    return SESSION.query(DBReport).filter(DBReport.topic == topic).all()


def get_reports_by_writer(write_by):
    return SESSION.query(DBReport).filter(DBReport.write_by == write_by).all()


def get_reports_by_type_and_writer(report_type, write_by):
    return (
        SESSION.query(DBReport)
        .filter(and_(DBReport.report_type == report_type, DBReport.write_by == write_by))
        .all()
    )


# 데이터 수정 (Update)
def update_report_content(report_id, new_content):
    report = SESSION.query(DBReport).filter(DBReport.report_id == report_id).first()
    if report:
        report.content = new_content
        SESSION.commit()


# 데이터 삭제 (Delete)
def delete_report_by_id(report_id):
    report = SESSION.query(DBReport).filter(DBReport.report_id == report_id).first()
    if report:
        SESSION.delete(report)
        SESSION.commit()


# report_type 기반 데이터 추출
def get_reports_by_report_type(report_type):
    return SESSION.query(DBReport).filter(DBReport.report_type == report_type).all()


# report_type과 write_by 기반 데이터 추출
def get_reports_by_type_and_writer(report_type, write_by):
    return (
        SESSION.query(DBReport)
        .filter(and_(DBReport.report_type == report_type, DBReport.write_by == write_by))
        .all()
    )


# report_type으로 group by 하여 카운트 얻기
def get_count_by_report_type():
    from sqlalchemy import func

    return (
        SESSION.query(DBReport.report_type, func.count(DBReport.report_id))
        .group_by(DBReport.report_type)
        .all()
    )


# write_by로 group by 하여 카운트 얻기
def get_count_by_writer():
    from sqlalchemy import func

    return (
        SESSION.query(DBReport.write_by, func.count(DBReport.report_id))
        .group_by(DBReport.write_by)
        .all()
    )


# 특정 report_type에 대한 write_by 별 카운트 얻기
def get_count_by_writer_for_type(report_type):
    from sqlalchemy import func

    return (
        SESSION.query(DBReport.write_by, func.count(DBReport.report_id))
        .filter(DBReport.report_type == report_type)
        .group_by(DBReport.write_by)
        .all()
    )
