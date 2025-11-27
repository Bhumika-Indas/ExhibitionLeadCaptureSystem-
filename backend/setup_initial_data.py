"""
Setup Initial Data Script
Creates default employee and exhibition for production use
"""

import pyodbc
from app.config import settings
import hashlib

def hash_password(password: str) -> str:
    """Return plain text password for development (no hashing)"""
    return password  # Plain text for development

def setup_initial_data():
    """Create initial employee and exhibition"""

    print("=" * 80)
    print(" SETUP INITIAL DATA")
    print("=" * 80)

    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = pyodbc.connect(settings.MSSQL_CONN_STRING, timeout=30)
        cursor = conn.cursor()
        print("Connected successfully!\n")

        # Create default employee
        print("Creating default employee...")

        full_name = input("Enter employee name (default: Admin User): ").strip() or "Admin User"
        mobile = input("Enter mobile number (default: 9876543210): ").strip() or "9876543210"
        email = input("Enter email (default: admin@indas.com): ").strip() or "admin@indas.com"
        password = input("Enter password (default: admin123): ").strip() or "admin123"

        password_hash = hash_password(password)

        # Check if employee exists
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE Phone = ?", (mobile,))
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"[INFO] Employee with mobile {mobile} already exists. Skipping.")
        else:
            cursor.execute("""
                INSERT INTO Employees (FullName, Phone, Email, LoginName, PasswordHash, IsActive)
                OUTPUT INSERTED.EmployeeId
                VALUES (?, ?, ?, ?, ?, 1)
            """, (full_name, mobile, email, mobile, password_hash))

            employee_id = cursor.fetchone()[0]
            print(f"[OK] Employee created successfully!")
            print(f"     ID: {employee_id}")
            print(f"     Name: {full_name}")
            print(f"     Mobile: {mobile}")
            print(f"     Email: {email}")
            print(f"     Password: {password}")

        print()

        # Create default exhibition
        print("Creating default exhibition...")

        exh_name = input("Enter exhibition name (default: Test Exhibition 2025): ").strip() or "Test Exhibition 2025"
        location = input("Enter location (default: India Expo Center): ").strip() or "India Expo Center"

        # Check if exhibition exists
        cursor.execute("SELECT COUNT(*) FROM Exhibitions WHERE Name = ?", (exh_name,))
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"[INFO] Exhibition '{exh_name}' already exists. Skipping.")
        else:
            cursor.execute("""
                INSERT INTO Exhibitions (Name, Location, StartDate, EndDate, IsActive)
                OUTPUT INSERTED.ExhibitionId
                VALUES (?, ?, GETDATE(), DATEADD(day, 7, GETDATE()), 1)
            """, (exh_name, location))

            exh_id = cursor.fetchone()[0]
            print(f"[OK] Exhibition created successfully!")
            print(f"     ID: {exh_id}")
            print(f"     Name: {exh_name}")
            print(f"     Location: {location}")

        # Commit changes
        conn.commit()
        print("\n" + "=" * 80)
        print("[SUCCESS] Initial data setup complete!")
        print("=" * 80)
        print("\nYou can now:")
        print(f"  1. Login with mobile: {mobile}")
        print(f"  2. Login with password: {password}")
        print(f"  3. Start uploading visiting cards!")
        print()

        # Close connection
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")

if __name__ == "__main__":
    setup_initial_data()
