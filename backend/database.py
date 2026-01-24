"""
MongoDB database configuration and connection.
Handles all database operations for claims storage.
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Dict, List, Optional
import os
from datetime import datetime


class MongoDB:
    """MongoDB client for claims database"""
    
    def __init__(self, connection_string: str, database_name: str = "insurance_claims"):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            print(f"[OK] Connected to MongoDB database: {self.database_name}")
        except ConnectionFailure as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        return self.db[collection_name]
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")


class ClaimsDB:
    """Database operations for claims"""
    
    def __init__(self, mongo_client: MongoDB):
        """
        Initialize claims database operations.
        
        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo = mongo_client
        self.claims_collection = self.mongo.get_collection("claims")
        self.policies_collection = self.mongo.get_collection("policies")
        
        # Create indexes for better query performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        try:
            # Index on claim_id for fast lookups
            self.claims_collection.create_index("claim_id", unique=True)
            
            # Index on policy_id for filtering claims by policy
            self.claims_collection.create_index("policy_id")
            
            # Index on decision status
            self.claims_collection.create_index("decision")
            
            # Index on submitted_at for sorting by date
            self.claims_collection.create_index("submitted_at")
            
            print("[OK] Database indexes created")
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    # ==================== CLAIM OPERATIONS ====================
    
    def insert_claim(self, claim_data: Dict) -> bool:
        """
        Insert a new claim into database.
        
        Args:
            claim_data: Claim data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.claims_collection.insert_one(claim_data)
            print(f"[OK] Claim {claim_data['claim_id']} inserted into database")
            return True
        except Exception as e:
            print(f"[ERROR] Error inserting claim: {e}")
            return False
    
    def get_claim(self, claim_id: str) -> Optional[Dict]:
        """
        Get a claim by ID.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            Claim data dictionary or None if not found
        """
        try:
            claim = self.claims_collection.find_one(
                {"claim_id": claim_id},
                {"_id": 0}  # Exclude MongoDB's internal ID
            )
            return claim
        except Exception as e:
            print(f"[ERROR] Error retrieving claim: {e}")
            return None
    
    def get_claims_by_policy(self, policy_id: str) -> List[Dict]:
        """
        Get all claims for a specific policy.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            List of claim dictionaries
        """
        try:
            claims = list(self.claims_collection.find(
                {"policy_id": policy_id},
                {"_id": 0}
            ).sort("submitted_at", -1))  # Sort by most recent first
            return claims
        except Exception as e:
            print(f"[ERROR] Error retrieving claims: {e}")
            return []
    
    def get_all_claims(self, limit: int = 100) -> List[Dict]:
        """
        Get all claims (limited).
        
        Args:
            limit: Maximum number of claims to return
            
        Returns:
            List of claim dictionaries
        """
        try:
            claims = list(self.claims_collection.find(
                {},
                {"_id": 0}
            ).sort("submitted_at", -1).limit(limit))
            return claims
        except Exception as e:
            print(f"[ERROR] Error retrieving claims: {e}")
            return []
    
    def update_claim(self, claim_id: str, update_data: Dict) -> bool:
        """
        Update a claim.
        
        Args:
            claim_id: Claim ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.claims_collection.update_one(
                {"claim_id": claim_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[ERROR] Error updating claim: {e}")
            return False
    
    def delete_claim(self, claim_id: str) -> bool:
        """
        Delete a claim.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.claims_collection.delete_one({"claim_id": claim_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ERROR] Error deleting claim: {e}")
            return False
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """
        Get claims statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            total_claims = self.claims_collection.count_documents({})
            
            approved = self.claims_collection.count_documents({"decision": "approved"})
            rejected = self.claims_collection.count_documents({"decision": "rejected"})
            under_review = self.claims_collection.count_documents({"decision": "under_review"})
            
            # Calculate total amounts using aggregation
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_claimed": {"$sum": "$claimed_amount"},
                        "total_approved": {"$sum": "$approved_amount"}
                    }
                }
            ]
            
            amounts = list(self.claims_collection.aggregate(pipeline))
            total_claimed = amounts[0]["total_claimed"] if amounts else 0
            total_approved = amounts[0]["total_approved"] if amounts else 0
            
            approval_rate = (approved / total_claims * 100) if total_claims > 0 else 0
            
            return {
                "total_claims": total_claims,
                "approved_claims": approved,
                "rejected_claims": rejected,
                "under_review_claims": under_review,
                "total_amount_claimed": total_claimed,
                "total_amount_approved": total_approved,
                "approval_rate": round(approval_rate, 2)
            }
        except Exception as e:
            print(f"[ERROR] Error getting statistics: {e}")
            return {
                "error": str(e),
                "total_claims": 0,
                "approved_claims": 0,
                "rejected_claims": 0,
                "under_review_claims": 0,
                "total_amount_claimed": 0.0,
                "total_amount_approved": 0.0,
                "approval_rate": 0.0
            }
    
    def get_claims_by_status(self, status: str) -> List[Dict]:
        """
        Get claims by decision status.
        
        Args:
            status: Decision status (approved/rejected/under_review)
            
        Returns:
            List of claim dictionaries
        """
        try:
            claims = list(self.claims_collection.find(
                {"decision": status},
                {"_id": 0}
            ).sort("submitted_at", -1))
            return claims
        except Exception as e:
            print(f"[ERROR] Error retrieving claims by status: {e}")
            return []
    
    # ==================== POLICY OPERATIONS ====================
    
    def store_policy_info(self, policy_id: str, policy_data: Dict) -> bool:
        """
        Store policy information extracted from documents.
        
        Args:
            policy_id: Policy ID
            policy_data: Policy information
            
        Returns:
            True if successful
        """
        try:
            self.policies_collection.update_one(
                {"policy_id": policy_id},
                {"$set": policy_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"[ERROR] Error storing policy info: {e}")
            return False
    

    def get_policy_info(self, policy_id: str) -> Optional[Dict]:
        """Get policy information"""
        try:
            policy = self.policies_collection.find_one(
                {"policy_id": policy_id},
                {"_id": 0}
            )
            return policy
        except Exception as e:
            print(f"[ERROR] Error retrieving policy: {e}")
            return None


class UsersDB:
    """Database operations for users"""
    
    def __init__(self, mongo_client: MongoDB):
        self.mongo = mongo_client
        self.users_collection = self.mongo.get_collection("users")
        self._create_indexes()
    
    def _create_indexes(self):
        try:
            self.users_collection.create_index("username", unique=True)
            self.users_collection.create_index("email", unique=True, sparse=True)
            print("[OK] User indexes created")
        except Exception as e:
            print(f"Warning: Could not create user indexes: {e}")

    def create_user(self, user_data: Dict) -> bool:
        try:
            self.users_collection.insert_one(user_data)
            return True
        except Exception as e:
            print(f"[ERROR] Error creating user: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict]:
        try:
            return self.users_collection.find_one({"username": username}, {"_id": 0})
        except Exception as e:
            print(f"[ERROR] Error getting user: {e}")
            return None


class DocumentsDB:
    """Database operations for document metadata"""
    
    def __init__(self, mongo_client: MongoDB):
        self.mongo = mongo_client
        self.documents_collection = self.mongo.get_collection("documents")
        self._create_indexes()
    
    def _create_indexes(self):
        try:
            self.documents_collection.create_index("doc_id", unique=True)
            self.documents_collection.create_index("user_id")
            print("[OK] Document indexes created")
        except Exception as e:
            print(f"Warning: Could not create document indexes: {e}")

    def save_document(self, doc_data: Dict) -> bool:
        try:
            # Convert Enum to string for MongoDB storage
            if 'doc_type' in doc_data and hasattr(doc_data['doc_type'], 'value'):
                doc_data['doc_type'] = doc_data['doc_type'].value
            if 'status' in doc_data and hasattr(doc_data['status'], 'value'):
                doc_data['status'] = doc_data['status'].value
                
            self.documents_collection.update_one(
                {"doc_id": doc_data["doc_id"]},
                {"$set": doc_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"[ERROR] Error saving document: {e}")
            return False

    def get_document(self, doc_id: str) -> Optional[Dict]:
        try:
            return self.documents_collection.find_one({"doc_id": doc_id}, {"_id": 0})
        except Exception as e:
            print(f"[ERROR] Error getting document: {e}")
            return None

    def get_user_documents(self, user_id: str) -> List[Dict]:
        try:
            return list(self.documents_collection.find({"user_id": user_id}, {"_id": 0}))
        except Exception as e:
            print(f"[ERROR] Error getting user documents: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        try:
            result = self.documents_collection.delete_one({"doc_id": doc_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ERROR] Error deleting document: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get document statistics"""
        try:
            total_docs = self.documents_collection.count_documents({})
            completed = self.documents_collection.count_documents({"status": "completed"})
            processing = self.documents_collection.count_documents({"status": "processing"})
            failed = self.documents_collection.count_documents({"status": "failed"})
            
            return {
                "total_documents": total_docs,
                "completed_documents": completed,
                "processing_documents": processing,
                "failed_documents": failed
            }
        except Exception as e:
            print(f"[ERROR] Error getting document stats: {e}")
            return {
                "total_documents": 0, "completed_documents": 0, 
                "processing_documents": 0, "failed_documents": 0
            }
