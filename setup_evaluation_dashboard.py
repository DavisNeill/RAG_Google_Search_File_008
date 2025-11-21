#!/usr/bin/env python3
"""
Evaluation Dashboard Setup Script
==================================

Automates the setup of evaluation dashboard:
1. Creates all database tables in Supabase
2. Makes specified user an admin

Usage:
    python setup_evaluation_dashboard.py your-email@example.com
"""

import os
import sys
import requests


def read_sql_schema():
    """Read the SQL schema file"""
    schema_path = 'evaluation_db_schema.sql'

    if not os.path.exists(schema_path):
        print(f"Error: {schema_path} not found!")
        print(f"Make sure you're running this script from the repository root directory.")
        sys.exit(1)

    with open(schema_path, 'r') as f:
        return f.read()


def execute_sql(supabase_url, supabase_key, sql):
    """Execute SQL via Supabase REST API"""
    # Remove the /rest/v1 suffix if present
    base_url = supabase_url.replace('/rest/v1', '')

    # Use PostgREST to execute SQL
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }

    # For executing SQL, we'll need to use the SQL endpoint
    url = f"{base_url}/rest/v1/rpc/exec_sql"

    try:
        response = requests.post(url, headers=headers, json={'query': sql})
        return response.status_code == 200
    except:
        return False


def setup_database_tables(supabase_url, supabase_key):
    """Create all evaluation database tables"""
    print("\n" + "="*60)
    print("STEP 1: Setting Up Database Tables")
    print("="*60)

    sql_schema = read_sql_schema()

    print("\n📋 SQL Schema loaded successfully!")
    print("\n⚠️  MANUAL STEP REQUIRED:")
    print("\nPlease follow these steps in Supabase Dashboard:")
    print("\n1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Click 'SQL Editor' in the left sidebar")
    print("4. Click 'New Query'")
    print("5. Copy and paste the contents of: evaluation_db_schema.sql")
    print("6. Click 'RUN' to execute")
    print("\nThis will create all required tables for the evaluation dashboard.")

    input("\nPress ENTER after you've completed this step...")

    print("\n✓ Database tables should now be created!")


def make_user_admin(supabase_url, supabase_key, email):
    """Make specified user an admin"""
    print("\n" + "="*60)
    print("STEP 2: Making User Admin")
    print("="*60)

    print(f"\nSetting admin privileges for: {email}")

    print("\n⚠️  MANUAL STEP REQUIRED:")
    print("\nPlease follow these steps in Supabase Dashboard:")
    print("\n1. Go to Supabase SQL Editor")
    print("2. Copy and paste this SQL query:")
    print("\n" + "-"*60)
    print(f"""
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
    COALESCE(raw_user_meta_data, '{{}}'::jsonb),
    '{{is_admin}}',
    'true'::jsonb
)
WHERE email = '{email}';
""")
    print("-"*60)
    print("\n3. Click 'RUN' to execute")
    print(f"\nThis will make {email} an admin user.")

    input("\nPress ENTER after you've completed this step...")

    print(f"\n✓ {email} should now have admin privileges!")


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🔬 EVALUATION DASHBOARD SETUP")
    print("="*60)

    # Check for email argument
    if len(sys.argv) < 2:
        print("\nUsage: python setup_evaluation_dashboard.py <your-email@example.com>")
        print("\nExample:")
        print("  python setup_evaluation_dashboard.py admin@example.com")
        print("\nThis will:")
        print("  1. Guide you through creating database tables")
        print("  2. Make the specified email an admin user")
        sys.exit(1)

    email = sys.argv[1]

    # Validate email format
    if '@' not in email or '.' not in email:
        print(f"\nError: '{email}' doesn't look like a valid email address")
        sys.exit(1)

    # Get Supabase credentials from environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("\nError: Supabase credentials not found!")
        print("\nPlease set environment variables:")
        print("  export SUPABASE_URL='your-supabase-url'")
        print("  export SUPABASE_KEY='your-supabase-key'")
        print("\nOr add them to your .env file")
        sys.exit(1)

    print(f"\n✓ Supabase URL: {supabase_url}")
    print(f"✓ Admin email: {email}")

    # Run setup steps
    try:
        # Step 1: Create database tables
        setup_database_tables(supabase_url, supabase_key)

        # Step 2: Make user admin
        make_user_admin(supabase_url, supabase_key, email)

        # Success message
        print("\n" + "="*60)
        print("✓ SETUP COMPLETED!")
        print("="*60)
        print("\n🎉 Next steps:")
        print("\n1. Start your Flask app:")
        print("   python app.py")
        print("\n2. Navigate to the evaluation dashboard:")
        print("   http://localhost:5000/evaluation/dashboard")
        print("\n3. You should now have admin access!")
        print("\n📚 For more information, see:")
        print("   EVALUATION_DASHBOARD_SETUP.md")
        print("\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        print("\nPlease check the error and try again.")
        sys.exit(1)


if __name__ == '__main__':
    main()
