import sys
import traceback

try:
    print("Starting server test...")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    
    print("\nImporting FastAPI...")
    from fastapi import FastAPI
    print("✓ FastAPI imported")
    
    print("\nImporting main module...")
    import main
    print("✓ Main module imported")
    
    print("\nStarting uvicorn...")
    import uvicorn
    uvicorn.run(main.app, host="127.0.0.1", port=8000, log_level="info")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
