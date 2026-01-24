"""
Quick test to verify MongoDB connection.
Run this to test before starting the server.
"""
from database import MongoDB, ClaimsDB
import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "insurance_claims")

print("=" * 60)
print("MongoDB Connection Test")
print("=" * 60)

if not MONGODB_URI:
    print("❌ No MONGODB_URI found in .env file")
    exit(1)

print(f"📡 Connecting to MongoDB...")
print(f"Database: {MONGODB_DATABASE}")

try:
    # Create MongoDB client
    mongo = MongoDB(MONGODB_URI, MONGODB_DATABASE)
    print("✅ MongoDB connection successful!")
    
    # Create claims database handler
    claims_db = ClaimsDB(mongo)
    print("✅ Claims database initialized!")
    
    # Test insert
    test_claim = {
        "claim_id": "TEST-001",
        "policy_id": "POL-TEST",
        "treatment_type": "test",
        "claimed_amount": 1000,
        "approved_amount": 1000,
        "decision": "approved",
        "explanation": "Test claim",
        "relevant_clauses": [],
        "submitted_at": "2024-12-03T00:00:00",
        "decided_at": "2024-12-03T00:00:00"
    }
    
    print("\n📝 Testing insert...")
    claims_db.insert_claim(test_claim)
    print("✅ Test claim inserted!")
    
    # Test retrieval
    print("\n📖 Testing retrieval...")
    retrieved = claims_db.get_claim("TEST-001")
    if retrieved:
        print("✅ Test claim retrieved!")
        print(f"   Claim ID: {retrieved['claim_id']}")
        print(f"   Policy ID: {retrieved['policy_id']}")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    stats = claims_db.get_statistics()
    print("✅ Statistics retrieved!")
    print(f"   Total claims: {stats['total_claims']}")
    
    # Clean up test claim
    print("\n🧹 Cleaning up...")
    claims_db.delete_claim("TEST-001")
    print("✅ Test claim deleted!")
    
    # Close connection
    mongo.close()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✨ Your MongoDB is ready to use!")
    print("   You can now start your server with confidence!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nPlease check:")
    print("1. MongoDB URI is correct")
    print("2. Internet connection is active")
    print("3. MongoDB Atlas cluster is running")
    exit(1)
