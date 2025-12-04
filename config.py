import os

class Config:
    """Configuration class for the medical system"""
    
    # Database configuration for AWS RDS MySQL
    DB_HOST = ''
    DB_PORT = xx
    DB_USER = ''
    DB_PASSWORD = ''
    DB_NAME = 'FHIR'
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'medical-system-secret-key-2024')
    DEBUG = True
    
    @staticmethod
    def get_db_config():
        """Return database configuration as dictionary"""
        return {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4',
            'autocommit': True
        }
