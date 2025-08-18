#!/usr/bin/env python3
"""
Simple script to check the database contents
"""

import sqlite3

def check_database():
    """Check the database contents"""
    conn = sqlite3.connect("scaleup_nvidia.db")
    cursor = conn.cursor()
    
    print("=== USERS TABLE ===")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"User: {user}")
    
    print("\n=== DOCKER IMAGES TABLE ===")
    cursor.execute("SELECT * FROM docker_images")
    images = cursor.fetchall()
    for image in images:
        print(f"Image: {image}")
    
    print(f"\nTotal users: {len(users)}")
    print(f"Total images: {len(images)}")
    
    # Check for duplicates
    cursor.execute("SELECT image_name, image_tag, user_id, COUNT(*) as count FROM docker_images GROUP BY image_name, image_tag, user_id HAVING COUNT(*) > 1")
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"\nDUPLICATES FOUND: {len(duplicates)}")
        for dup in duplicates:
            print(f"Duplicate: {dup}")
    else:
        print("\nNo duplicates found in database")
    
    conn.close()

if __name__ == "__main__":
    check_database()
