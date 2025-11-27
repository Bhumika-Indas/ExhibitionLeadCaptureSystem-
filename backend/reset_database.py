"""
Reset Database Script
Deletes all data from lead-related tables and resets identity columns
"""

import pyodbc
import sys
from app.config import settings

def reset_database():
    """Delete all data and reset identity columns"""

    print("=" * 80)
    print(" RESETTING DATABASE - ALL LEAD DATA WILL BE DELETED")
    print(" (Employees data will be PRESERVED)")
    print("=" * 80)

    # Confirm before proceeding
    confirm = input("\nAre you sure you want to delete ALL LEAD data? Type 'YES' to confirm: ")
    if confirm != "YES":
        print("Aborted. No changes made.")
        return

    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = pyodbc.connect(settings.MSSQL_CONN_STRING, timeout=30)
        cursor = conn.cursor()

        print("Connected successfully!\n")

        # List of tables to clear (in order due to foreign key constraints)
        # NOTE: Employees, Exhibitions, and Lookup tables are NOT included - will be preserved
        tables_to_clear = [
            # WhatsApp and messaging tables
            "WhatsAppMessages",      # Child of Leads (includes LID tracking)
            "LeadMessages",          # Child of Leads

            # Attachments
            "LeadAttachments",       # Child of Leads (if exists)
            "Attachments",           # Child of Leads

            # Lead details tables (multi-contact support)
            "LeadBrands",            # Child of Leads (dealer brands)
            "LeadPhones",            # Child of Leads (multiple phones)
            "LeadEmails",            # Child of Leads (multiple emails)
            "LeadWebsites",          # Child of Leads
            "LeadServices",          # Child of Leads
            "LeadTopics",            # Child of Leads
            "LeadPersons",           # Child of Leads
            "LeadAddresses",         # Child of Leads

            # Follow-ups and drip campaigns
            "DripEnrollments",       # Child of Leads (drip sequence enrollments)
            "FollowUps",             # Child of Leads

            # Main leads table
            "Leads"                  # Parent table
        ]

        print("Deleting data from tables...")
        print("-" * 80)

        for table in tables_to_clear:
            try:
                # Delete all rows
                cursor.execute(f"DELETE FROM {table}")
                deleted_count = cursor.rowcount
                print(f"[OK] {table}: Deleted {deleted_count} rows")

                # Reset identity column to start from 1
                cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
                print(f"     -> Identity column reset to start from 1")

            except pyodbc.Error as e:
                print(f"[SKIP] {table}: Error - {e}")

        # Commit all changes
        conn.commit()
        print("-" * 80)
        print("\n[SUCCESS] Database reset complete!")
        print("Next lead will have LeadId = 1\n")

        # Close connection
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    reset_database()
