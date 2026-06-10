import pymysql
import motor.motor_asyncio
import os
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error("Failed to connect to MySQL")
        raise e

def execute_query(query: str, params: tuple = None):
    """
    Executes a query using parameterized queries to prevent SQL injection.
    """
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        connection.commit()
        return result
    except Exception as e:
        logger.error(f"Database query error")
        raise e
    finally:
        connection.close()

@contextmanager
def mysql_transaction():
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

try:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    
    behavior_logs_collection = mongo_db.get_collection("pokemon_behavior_logs")
    incident_reports_collection = mongo_db.get_collection("incident_reports")
    visitor_reviews_collection = mongo_db.get_collection("visitor_reviews")
    
except Exception as e:
    logger.error("Failed to connect to MongoDB")

async def get_mongo_db():
    return mongo_db
