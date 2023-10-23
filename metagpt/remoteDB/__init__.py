from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from metagpt.config import CONFIG

DBBASE = declarative_base()
DBENGINE = create_engine(CONFIG.db_addr)

session = sessionmaker(bind=DBENGINE)
SESSION = session()


def init_db():
    from .reportdb import DBReport

    DBBASE.metadata.create_all(DBENGINE)
