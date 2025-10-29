"""
Database connection and management
"""
import os
import time
import pymongo
from dotenv import load_dotenv

load_dotenv()


class Database:
    """MongoDB database connection manager with retry logic and connection pooling (Singleton)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only create one instance"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection (only once)"""
        if Database._initialized:
            return  # Already initialized, skip
        
        self.client = None
        self.patients_collection = None
        self.mental_health_collection = None
        self.doctors_collection = None
        self.doctor_v2_collection = None
        self.invite_codes_collection = None
        self.connect()
        Database._initialized = True
    
    def connect(self):
        """Connect to MongoDB with retry logic"""
        if self.client and self.patients_collection:
            return  # Already connected
        
        max_retries = 3
        retry_count = 0
        start_time = time.time()
        
        # Control verbosity
        verbose = os.getenv('DB_VERBOSE', 'false').lower() == 'true'
        
        while retry_count < max_retries:
            try:
                mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
                db_name = os.getenv("DB_NAME", "patients_db")
                
                # Minimal output - only on first attempt
                if retry_count == 0:
                    print("[*] Database Connection")
                    if verbose:
                        print(f"    |-- URI: {mongo_uri}")
                    print(f"    |-- Connecting to: {db_name}...")
                
                # Close existing connection if any
                if self.client:
                    try:
                        self.client.close()
                    except:
                        pass
                
                self.client = pymongo.MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    connectTimeoutMS=10000
                )
                
                # Test connection (silent)
                self.client.admin.command('ping')
                
                # Get database
                db_instance = self.client[db_name]
                
                # Initialize collections
                # Support both COLLECTION_NAME and Patient_COLLECTION_NAME for flexibility
                collection_name = os.getenv("Patient_COLLECTION_NAME") or os.getenv("COLLECTION_NAME", "Patient_test")
                mental_health_collection_name = os.getenv("MENTAL_HEALTH_COLLECTION", "mental_health_logs")
                
                self.patients_collection = db_instance[collection_name]
                self.mental_health_collection = db_instance[mental_health_collection_name]
                self.doctors_collection = db_instance.get_collection('doctors')
                self.doctor_v2_collection = db_instance.get_collection('doctor_v2')
                self.invite_codes_collection = db_instance.get_collection('invite_codes')
                
                # Create indexes (silent)
                self._create_indexes_silent()
                
                # Calculate connection time
                connect_time = time.time() - start_time
                
                # Clean success output
                print(f"    |-- Status: [OK] Connected")
                print(f"    |-- Database: {db_name}")
                print(f"    |-- Collections: {collection_name}, {mental_health_collection_name}, invite_codes")
                if verbose:
                    print(f"    |-- Time: {connect_time:.2f}s")
                print("")
                return  # Success, exit the retry loop
                
            except Exception as e:
                retry_count += 1
                print(f"    |-- Attempt {retry_count} failed: {str(e)[:80]}")
                
                if retry_count >= max_retries:
                    print(f"    |-- Status: [FAILED] after {max_retries} attempts")
                    print("")
                    self.patients_collection = None
                    self.mental_health_collection = None
                else:
                    time.sleep(2)
    
    def _create_indexes_silent(self):
        """Create database indexes (silent mode)"""
        try:
            # Patients collection indexes
            self.patients_collection.create_index("patient_id", unique=True, sparse=True)
            self.patients_collection.create_index("email", unique=True, sparse=True)
            self.patients_collection.create_index("mobile", unique=True, sparse=True)
            
            # Mental health collection indexes
            try:
                self.mental_health_collection.drop_indexes()
            except:
                pass  # Ignore if no indexes exist
            
            self.mental_health_collection.create_index("patient_id")
            self.mental_health_collection.create_index("date")
            self.mental_health_collection.create_index([("patient_id", 1), ("date", 1), ("type", 1)])
            
            # Invite codes collection indexes
            self.invite_codes_collection.create_index("invite_code", unique=True)
            self.invite_codes_collection.create_index("doctor_id")
            self.invite_codes_collection.create_index("patient_email")
            self.invite_codes_collection.create_index("status")
            self.invite_codes_collection.create_index("expires_at")
            
            # Only show if verbose
            if os.getenv('DB_VERBOSE', 'false').lower() == 'true':
                print("    |-- Indexes: [OK] Created")
            
        except Exception as e:
            print(f"    |-- Index warning: {e}")
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
    
    def is_connected(self):
        """Check if database is connected and accessible"""
        try:
            if self.client is None or self.patients_collection is None:
                return False
            
            # Test connection with a simple command
            self.client.admin.command('ping')
            return True
        except:
            return False
    
    def reconnect(self):
        """Attempt to reconnect to the database"""
        print("[*] Reconnecting to database...")
        self.connect()
        return self.is_connected()
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        if self.client:
            db_name = os.getenv("DB_NAME", "patients_db")
            return self.client[db_name][collection_name]
        return None


# Global singleton instance - import this instead of creating new Database()
db = Database()

