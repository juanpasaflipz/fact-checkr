#!/usr/bin/env python3
"""
Migrate data from Supabase to Neon database.

This script:
1. Connects to Supabase (if connection string provided)
2. Exports all data
3. Imports data to Neon
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

load_dotenv()

def get_table_data(engine, table_name):
    """Export all data from a table"""
    with engine.connect() as conn:
        # Get column names
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Get all rows
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Handle datetime serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, '__dict__'):  # Handle enums
                    value = str(value)
                row_dict[col] = value
            data.append(row_dict)
        
        return data

def insert_table_data(engine, table_name, data):
    """Insert data into a table"""
    if not data:
        return 0
    
    import json
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    inserted = 0
    for row in data:
        # Use individual connections to avoid transaction issues
        with engine.connect() as conn:
            try:
                # Build INSERT statement with ON CONFLICT DO NOTHING
                cols = ', '.join(columns)
                placeholders = ', '.join([f':{col}' for col in columns])
                
                # Handle special cases
                values = {}
                for col in columns:
                    val = row.get(col)
                    # Convert lists/arrays to JSON strings for JSON columns
                    if col == 'evidence_sources' and isinstance(val, list):
                        values[col] = json.dumps(val)
                    elif isinstance(val, str) and val.startswith('20'):  # ISO datetime string
                        values[col] = val
                    else:
                        values[col] = val
                
                # Use ON CONFLICT for tables with primary keys
                if table_name in ['sources', 'claims', 'topics', 'entities']:
                    stmt = f"""
                        INSERT INTO {table_name} ({cols})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                    """
                else:
                    stmt = f"""
                        INSERT INTO {table_name} ({cols})
                        VALUES ({placeholders})
                    """
                
                conn.execute(text(stmt), values)
                conn.commit()
                inserted += 1
            except Exception as e:
                error_msg = str(e)
                # Only show first error to avoid spam
                if inserted == 0:
                    print(f"  ⚠ Warning: Failed to insert row in {table_name}: {error_msg[:150]}")
                conn.rollback()
                continue
    
    return inserted

def migrate_data(supabase_url, neon_url):
    """Migrate data from Supabase to Neon"""
    
    print("🔄 Starting data migration from Supabase to Neon")
    print("=" * 60)
    
    # Connect to Supabase
    print("\n1. Connecting to Supabase...")
    try:
        supabase_engine = create_engine(supabase_url)
        with supabase_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Supabase connection successful")
    except Exception as e:
        print(f"   ❌ Failed to connect to Supabase: {e}")
        return False
    
    # Connect to Neon
    print("\n2. Connecting to Neon...")
    try:
        neon_engine = create_engine(neon_url)
        with neon_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Neon connection successful")
    except Exception as e:
        print(f"   ❌ Failed to connect to Neon: {e}")
        return False
    
    # Get list of tables to migrate
    print("\n3. Identifying tables to migrate...")
    inspector = inspect(supabase_engine)
    tables = inspector.get_table_names()
    
    # Filter out system tables
    tables_to_migrate = [t for t in tables if not t.startswith('_') and t != 'alembic_version']
    print(f"   Found {len(tables_to_migrate)} tables: {', '.join(tables_to_migrate)}")
    
    # Migrate each table
    print("\n4. Migrating data...")
    total_rows = 0
    
    for table in tables_to_migrate:
        try:
            # Export from Supabase
            print(f"\n   📤 Exporting {table}...")
            data = get_table_data(supabase_engine, table)
            print(f"      Found {len(data)} rows")
            
            if data:
                # Import to Neon
                print(f"   📥 Importing {table}...")
                inserted = insert_table_data(neon_engine, table, data)
                print(f"      ✅ Inserted {inserted} rows")
                total_rows += inserted
            else:
                print(f"      ⚠ No data to migrate")
                
        except Exception as e:
            print(f"   ❌ Error migrating {table}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print(f"✅ Migration complete! Migrated {total_rows} total rows")
    
    # Verify data
    print("\n5. Verifying migration...")
    for table in tables_to_migrate:
        try:
            supabase_count = len(get_table_data(supabase_engine, table))
            neon_count = len(get_table_data(neon_engine, table))
            
            status = "✅" if supabase_count == neon_count else "⚠"
            print(f"   {status} {table}: Supabase={supabase_count}, Neon={neon_count}")
        except Exception as e:
            print(f"   ❌ Error verifying {table}: {e}")
    
    return True

if __name__ == "__main__":
    # Get connection strings
    supabase_url = os.getenv("SUPABASE_DATABASE_URL")
    neon_url = os.getenv("DATABASE_URL")
    
    if not supabase_url:
        print("❌ Error: SUPABASE_DATABASE_URL not found in environment")
        print("\nPlease provide your Supabase connection string:")
        print("Option 1: Add to .env file:")
        print("  SUPABASE_DATABASE_URL=postgresql://user:pass@host/db")
        print("\nOption 2: Pass as argument:")
        print("  SUPABASE_DATABASE_URL='...' python migrate_data_supabase_to_neon.py")
        sys.exit(1)
    
    if not neon_url:
        print("❌ Error: DATABASE_URL (Neon) not found in environment")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    # Run migration
    success = migrate_data(supabase_url, neon_url)
    
    if success:
        print("\n🎉 Data migration completed successfully!")
        print("\nNext steps:")
        print("1. Verify data in Neon dashboard")
        print("2. Test your application")
        print("3. Remove SUPABASE_DATABASE_URL from .env if no longer needed")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)

