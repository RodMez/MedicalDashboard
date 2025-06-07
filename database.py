import pymysql
import logging
from config import Config
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for MySQL connections"""
    
    def __init__(self):
        self.config = Config.get_db_config()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = pymysql.connect(**self.config)
            logger.debug("Database connection established")
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(query, params or ())
                    results = cursor.fetchall()
                    logger.debug(f"Query executed successfully: {len(results)} rows returned")
                    return results
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return []
    
    def execute_single_query(self, query, params=None):
        """Execute a SELECT query and return single result"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(query, params or ())
                    result = cursor.fetchone()
                    logger.debug("Single query executed successfully")
                    return result
        except Exception as e:
            logger.error(f"Single query execution error: {e}")
            return None

# Global database manager instance
db_manager = DatabaseManager()
