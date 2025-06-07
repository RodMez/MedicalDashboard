import os

class Config:
    """Configuration class for the medical system"""
    
    # Database configuration for AWS RDS MySQL
    DB_HOST = 'datafhirdb.czmak2qwe489.us-east-2.rds.amazonaws.com'
    DB_PORT = 3306
    DB_USER = 'admin'
    DB_PASSWORD = 'fhirpass'
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
