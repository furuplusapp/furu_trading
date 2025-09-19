#!/usr/bin/env python3
"""
Script to run the migration step by step
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

def run_migration():
    load_dotenv()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("ERROR: .env file not found")
        print("Please copy env.example to .env and configure your database settings")
        return False
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in .env file")
        return False
    
    print(f"Database URL: {database_url}")
    
    try:
        # Step 1: Check current migration status
        print("\n=== Step 1: Checking current migration status ===")
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True)
        print(f"Current status: {result.stdout.strip()}")
        if result.stderr:
            print(f"Warnings: {result.stderr.strip()}")
        
        # Step 2: Show migration history
        print("\n=== Step 2: Migration history ===")
        result = subprocess.run(['alembic', 'history'], capture_output=True, text=True)
        print(result.stdout)
        
        # Step 3: Try to run the migration
        print("\n=== Step 3: Running migration ===")
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Migration completed successfully!")
            print(result.stdout)
        else:
            print("✗ Migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
            # If migration failed, try to reset and retry
            print("\n=== Attempting to reset and retry ===")
            
            # Reset alembic version table
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM alembic_version;"))
                    print("✓ Reset alembic_version table")
            except Exception as e:
                print(f"Could not reset alembic_version: {e}")
            
            # Try migration again
            result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Migration completed successfully on retry!")
                print(result.stdout)
            else:
                print("✗ Migration still failed after reset")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)