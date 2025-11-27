"""
Reset ALL Database Tables Script
Deletes all data from ALL tables except authentication/lookup tables
USE WITH CAUTION - This will delete EVERYTHING including exhibitions, employees (except auth)
"""

import pyodbc
import sys
from app.config import settings

def reset_all_tables():
    """Delete all data from all tables except core lookup/auth tables"""

    print("=" * 80)
    print(" RESETTING ALL DATABASE TABLES - ALL DATA WILL BE DELETED")
    print(" (Only core lookup tables like LeadSources, LeadStatuses will be preserved)")
    print("=" * 80)

    # Confirm before proceeding
    confirm = input("\nType 'DELETE EVERYTHING' to confirm: ")
    if confirm != "DELETE EVERYTHING":
        print("Aborted. No changes made.")
        return

    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = pyodbc.connect(settings.MSSQL_CONN_STRING, timeout=30)
        cursor = conn.cursor()

        print("Connected successfully!\n")

        # List of tables to clear (in correct order due to foreign key constraints)
        # IMPORTANT: Lookup tables (LeadSources, LeadStatuses, DripActionTypes) are preserved
        tables_to_clear = [
            # Drip campaign tables (must be first due to FK)
            "ScheduledDripMessages",     # Child of DripEnrollments
            "DripMessages",              # Child of DripMaster
            "DripEnrollments",           # Child of Leads + DripMaster
            "DripMaster",                # Templates

            # WhatsApp and messaging tables
            "WhatsAppMessages",          # Child of Leads
            "LeadMessages",              # Child of Leads
            "Messages",                  # Alternative name for LeadMessages

            # Attachments
            "LeadAttachments",           # Child of Leads
            "Attachments",               # Alternative name

            # Lead details tables (multi-contact support)
            "LeadBrands",                # Child of Leads (dealer brands)
            "LeadPhones",                # Child of Leads (multiple phones)
            "LeadEmails",                # Child of Leads (multiple emails)
            "LeadWebsites",              # Child of Leads
            "LeadServices",              # Child of Leads
            "LeadTopics",                # Child of Leads
            "LeadPersons",               # Child of Leads
            "LeadAddresses",             # Child of Leads

            # Follow-ups
            "FollowUps",                 # Child of Leads
            "NextStepActions",           # Next step tracking

            # Main leads table
            "Leads",                     # Parent table

            # Exhibitions (if you want to reset these too)
            "Exhibitions",               # Exhibition events

            # Employees (reset employee data but keep the structure)
            "Employees",                 # Employee accounts

            # Message templates
            "MessageTemplates",          # Template library
        ]

        print("Deleting data from tables...")
        print("-" * 80)

        deleted_tables = []
        skipped_tables = []

        for table in tables_to_clear:
            try:
                # Delete all rows
                cursor.execute(f"DELETE FROM {table}")
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    print(f"[OK] {table}: Deleted {deleted_count} rows")
                    deleted_tables.append(table)
                else:
                    print(f"[OK] {table}: Already empty (0 rows)")
                    deleted_tables.append(table)

                # Reset identity column to start from 1
                try:
                    cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
                    print(f"     -> Identity column reset to start from 1")
                except:
                    pass  # Some tables don't have identity columns

            except pyodbc.Error as e:
                error_msg = str(e)
                if "Invalid object name" in error_msg:
                    print(f"[SKIP] {table}: Table does not exist")
                else:
                    print(f"[SKIP] {table}: Error - {error_msg[:100]}")
                skipped_tables.append(table)

        # Commit all changes
        conn.commit()
        print("-" * 80)
        print(f"\n[SUCCESS] Database reset complete!")
        print(f"Tables cleared: {len(deleted_tables)}")
        print(f"Tables skipped: {len(skipped_tables)}")

        print("\nPreserved lookup tables:")
        print("  - LeadSources (source types)")
        print("  - LeadStatuses (status types)")
        print("  - DripActionTypes (drip action types)")
        print()

        print("All data cleared from:")
        for table in deleted_tables[:10]:  # Show first 10
            print(f"  - {table}")
        if len(deleted_tables) > 10:
            print(f"  ... and {len(deleted_tables) - 10} more tables")
        print()

        # Close connection
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    reset_all_tables()
