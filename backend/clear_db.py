#!/usr/bin/env python3
"""
Script to clear the database and start fresh
"""

import sqlite3
import os

def clear_database():
    """Clear the database and start fresh"""
    db_path = "scaleup_nvidia.db"
    
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
        print("Database removed successfully")
    else:
        print("No existing database found")
    
    # Reinitialize the database
    from simple_server import init_database
    init_database()
    print("Database reinitialized successfully")

if __name__ == "__main__":
    clear_database()
