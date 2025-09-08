from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import logging

Base = declarative_base()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, url: str = "sqlite:///./data/msg_db/messages.db"):
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info("Database initialized with URL: %s", url)

    def init_db(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created.")

    def get_session(self) -> Session:
        logger.debug("Creating new database session.")
        return self.SessionLocal()
