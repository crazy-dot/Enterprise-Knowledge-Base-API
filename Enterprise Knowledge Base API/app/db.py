from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker
import sys

def get_connection():
    try:
        engine = create_engine('postgresql+psycopg2://postgres:root@localhost:5432/document_reader')
        Session = sessionmaker(bind=engine)
        return engine, Session
    except Exception as e:
        print("Unable to connect to database.")
        sys.exit(1)


