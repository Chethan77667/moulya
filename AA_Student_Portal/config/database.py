"""
MongoDB Database Configuration
=============================

This module handles MongoDB connection and configuration for the Student Portal.
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional


class MongoDBConfig:
    """MongoDB configuration and connection management"""
    
    def __init__(self):
        """Initialize MongoDB configuration"""
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = os.getenv('MONGODB_DATABASE', 'moulya')
        self.collection_name = os.getenv('MONGODB_COLLECTION', 'login_credentials')
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
    
    def connect(self) -> bool:
        """
        Connect to MongoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            return True
            
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected MongoDB error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    def get_collection(self):
        """Get the login credentials collection"""
        if not self.collection:
            self.connect()
        return self.collection
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False


# Global MongoDB instance
mongodb_config = MongoDBConfig()
