# Visibility Control Features

This document describes the two new admin-controlled visibility features added to the Agentic RAG system.

## Table of Contents
- [Overview](#overview)
- [Feature 1: User Analytics Visibility Control](#feature-1-user-analytics-visibility-control)
- [Feature 2: Knowledge Base Visibility Control](#feature-2-knowledge-base-visibility-control)
- [Setup Instructions](#setup-instructions)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Security Considerations](#security-considerations)

---

## Overview

Two new admin-controlled visibility features have been implemented:

1. **Analytics Visibility Control**: Admins can control which users can view their memory analytics (hidden by default)
2. **Knowledge Base Visibility Control**: Admins can hide knowledge bases from listings while keeping them queryable

Both features provide granular control over data visibility while maintaining functionality.

---

## Feature 1: User Analytics Visibility Control

### Description

User analytics are **hidden by default**. Admins can enable/disable analytics visibility for individual users or in bulk.

### Key Behaviors

- ✅ Analytics are **disabled by default** for all new users
- ✅ Users can only see their analytics if explicitly enabled by an admin
- ✅ Admins can always view all analytics regardless of settings
- ✅ Users attempting to access disabled analytics receive a clear error message
- ✅ Tracks who changed visibility and when

### Database Schema

```sql
-- Added to user_profiles table
ALTER TABLE user_profiles ADD COLUMN analytics_visible BOOLEAN DEFAULT false;
ALTER TABLE user_profiles ADD COLUMN analytics_visibility_updated_by UUID REFERENCES auth.users(id);
ALTER TABLE user_profiles ADD COLUMN analytics_visibility_updated_at TIMESTAMP WITH TIME ZONE;
```

### Admin Endpoints

#### Enable Analytics for a User
```http
POST /api/admin/analytics/enable/<user_id>
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "message": "Analytics enabled for user <user_id>"
}
```

#### Disable Analytics for a User
```http
POST /api/admin/analytics/disable/<user_id>
Authorization: Admin required
```

#### Bulk Enable
```http
POST /api/admin/analytics/bulk-enable
Content-Type: application/json
Authorization: Admin required

{
  "user_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Analytics enabled for 3 user(s)",
  "updated_count": 3
}
```

#### Bulk Disable
```http
POST /api/admin/analytics/bulk-disable
Content-Type: application/json
Authorization: Admin required

{
  "user_ids": ["uuid1", "uuid2"]
}
```

#### Check Status
```http
GET /api/admin/analytics/status/<user_id>
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "user_id": "uuid",
  "analytics_visible": true,
  "updated_by": "admin-uuid",
  "updated_at": "2025-01-20T10:30:00Z"
}
```

#### List All Users
```http
GET /api/admin/users/list
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "uuid1",
      "email": "user1@example.com",
      "role": "user",
      "analytics_visible": false,
      "created_at": "2025-01-15T08:00:00Z"
    },
    {
      "id": "uuid2",
      "email": "user2@example.com",
      "role": "user",
      "analytics_visible": true,
      "created_at": "2025-01-16T09:00:00Z"
    }
  ],
  "count": 2
}
```

### User Experience

**When Analytics are Disabled:**
```http
GET /api/memory/analytics
```

**Response (403 Forbidden):**
```json
{
  "error": "Analytics are not enabled for your account. Contact an administrator.",
  "analytics_enabled": false
}
```

**When Analytics are Enabled:**
```http
GET /api/memory/analytics
```

**Response (200 OK):**
```json
{
  "success": true,
  "analytics_enabled": true,
  "analytics": {
    "total_memories": 150,
    "query_type_distribution": {
      "FACTUAL": 60,
      "ANALYTICAL": 45,
      "GENERAL": 45
    },
    "activity_by_day": {
      "2025-01-20": 25,
      "2025-01-19": 30
    },
    "recent_activity": 150
  }
}
```

---

## Feature 2: Knowledge Base Visibility Control

### Description

Admins can hide knowledge bases from listings while **keeping them fully queryable**. This allows for controlled access to sensitive knowledge bases without removing functionality.

### Key Behaviors

- ✅ Knowledge bases are **visible by default**
- ✅ Hidden knowledge bases don't appear in store listings for regular users
- ✅ Hidden knowledge bases **remain fully queryable** if the user knows the store ID
- ✅ Admins can see all knowledge bases (hidden or visible)
- ✅ Tracks who hid the knowledge base and when

### Database Schema

```sql
-- Added to user_vector_stores table
ALTER TABLE user_vector_stores ADD COLUMN is_visible BOOLEAN DEFAULT true;
ALTER TABLE user_vector_stores ADD COLUMN hidden_by UUID REFERENCES auth.users(id);
ALTER TABLE user_vector_stores ADD COLUMN hidden_at TIMESTAMP WITH TIME ZONE;
```

### Admin Endpoints

#### Hide Knowledge Base
```http
POST /api/admin/knowledge-base/hide/<store_id>
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "message": "Knowledge base hidden from list (still queryable)"
}
```

#### Show Knowledge Base
```http
POST /api/admin/knowledge-base/show/<store_id>
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "message": "Knowledge base is now visible in list"
}
```

#### Bulk Hide
```http
POST /api/admin/knowledge-base/bulk-hide
Content-Type: application/json
Authorization: Admin required

{
  "store_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully hid 3 knowledge base(s)",
  "updated_count": 3
}
```

#### Bulk Show
```http
POST /api/admin/knowledge-base/bulk-show
Content-Type: application/json
Authorization: Admin required

{
  "store_ids": ["uuid1", "uuid2"]
}
```

#### Get All Knowledge Bases (Admin)
```http
GET /api/admin/knowledge-base/all
Authorization: Admin required
```

**Response:**
```json
{
  "success": true,
  "stores": [
    {
      "id": "uuid1",
      "store_id": "gemini-store-id-1",
      "store_name": "public_docs",
      "description": "Public documentation",
      "is_visible": true,
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "uuid2",
      "store_id": "gemini-store-id-2",
      "store_name": "confidential_docs",
      "description": "Confidential documents",
      "is_visible": false,
      "hidden_by": "admin-uuid",
      "hidden_at": "2025-01-18T14:30:00Z"
    }
  ],
  "count": 2
}
```

### User Endpoints

#### Get Visible Knowledge Bases
```http
GET /api/knowledge-base/visible
Authorization: User required
```

**Response (Regular User):**
```json
{
  "success": true,
  "stores": [
    {
      "id": "uuid1",
      "store_id": "gemini-store-id-1",
      "store_name": "public_docs",
      "description": "Public documentation"
    }
  ],
  "count": 1
}
```

Note: Hidden stores are not included for regular users.

#### List Stores (Updated)
```http
GET /stores
```

**Admin Response:**
```json
{
  "stores": [
    {
      "id": "uuid1",
      "store_id": "gemini-store-id-1",
      "store_name": "public_docs",
      "description": "Public documentation",
      "is_visible": true
    },
    {
      "id": "uuid2",
      "store_id": "gemini-store-id-2",
      "store_name": "confidential_docs",
      "description": "Confidential documents",
      "is_visible": false
    }
  ],
  "count": 2
}
```

**Regular User Response:**
```json
{
  "stores": [
    {
      "id": "uuid1",
      "store_id": "gemini-store-id-1",
      "store_name": "public_docs",
      "description": "Public documentation"
    }
  ],
  "count": 1
}
```

### Querying Hidden Knowledge Bases

**Important:** Even when hidden from listings, knowledge bases can still be queried if the user knows the store ID:

```http
POST /query
Content-Type: application/json
Authorization: User required

{
  "question": "What information is in the confidential docs?",
  "store_name": "default"
}
```

This allows for controlled access where users can query if they know the store exists, but it won't be advertised in the UI.

---

## Setup Instructions

### 1. Run Database Migration

Execute the new schema in your Supabase SQL Editor:

```bash
# Apply the visibility features schema
psql -f database_schema_visibility_features.sql
```

Or copy the contents of `database_schema_visibility_features.sql` into the Supabase SQL Editor and execute.

### 2. Verify Database Changes

Check that the new columns were added:

```sql
-- Check user_profiles
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles'
  AND column_name IN ('analytics_visible', 'analytics_visibility_updated_by', 'analytics_visibility_updated_at');

-- Check user_vector_stores
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_vector_stores'
  AND column_name IN ('is_visible', 'hidden_by', 'hidden_at');
```

### 3. Update Application

The application code (`app.py`) has been updated with the new endpoints. No additional changes needed.

### 4. Test the Features

```bash
# Start the application
python app.py

# Log in as admin
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your-password"}'

# List all users
curl http://localhost:5000/api/admin/users/list \
  -H "Cookie: session=your-session-cookie"

# Enable analytics for a user
curl -X POST http://localhost:5000/api/admin/analytics/enable/<user-id> \
  -H "Cookie: session=your-session-cookie"

# Hide a knowledge base
curl -X POST http://localhost:5000/api/admin/knowledge-base/hide/<store-id> \
  -H "Cookie: session=your-session-cookie"
```

---

## Usage Examples

### Example 1: Enable Analytics for New Users

```python
import requests

# Admin login
session = requests.Session()
login_response = session.post('http://localhost:5000/api/auth/login', json={
    'email': 'admin@example.com',
    'password': 'admin-password'
})

# Get all users
users_response = session.get('http://localhost:5000/api/admin/users/list')
users = users_response.json()['users']

# Find users with disabled analytics
disabled_users = [u['id'] for u in users if not u['analytics_visible']]

# Enable analytics for all
if disabled_users:
    enable_response = session.post('http://localhost:5000/api/admin/analytics/bulk-enable', json={
        'user_ids': disabled_users
    })
    print(f"Enabled analytics for {enable_response.json()['updated_count']} users")
```

### Example 2: Hide Sensitive Knowledge Bases

```python
import requests

session = requests.Session()
session.post('http://localhost:5000/api/auth/login', json={
    'email': 'admin@example.com',
    'password': 'admin-password'
})

# Get all knowledge bases
kb_response = session.get('http://localhost:5000/api/admin/knowledge-base/all')
all_stores = kb_response.json()['stores']

# Hide knowledge bases containing "confidential" or "internal"
sensitive_stores = [
    s['id'] for s in all_stores
    if 'confidential' in s['store_name'].lower() or 'internal' in s['store_name'].lower()
]

if sensitive_stores:
    hide_response = session.post('http://localhost:5000/api/admin/knowledge-base/bulk-hide', json={
        'store_ids': sensitive_stores
    })
    print(f"Hid {hide_response.json()['updated_count']} sensitive knowledge bases")
```

### Example 3: User Tries to Access Disabled Analytics

```python
import requests

# Regular user login
session = requests.Session()
session.post('http://localhost:5000/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'user-password'
})

# Try to access analytics
analytics_response = session.get('http://localhost:5000/api/memory/analytics')

if analytics_response.status_code == 403:
    print("Analytics are disabled for this user")
    print(analytics_response.json()['error'])
    # Output: "Analytics are not enabled for your account. Contact an administrator."
```

---

## Security Considerations

### Analytics Visibility

1. **Default Deny**: Analytics are disabled by default for privacy
2. **Admin Only**: Only admins can enable/disable analytics visibility
3. **Audit Trail**: System tracks who enabled/disabled analytics and when
4. **Self Access**: Users can only access their own analytics (if enabled)
5. **Admin Override**: Admins can always view all analytics

### Knowledge Base Visibility

1. **Queryable by Design**: Hidden knowledge bases remain queryable for legitimate use cases
2. **Admin Control**: Only admins can hide/show knowledge bases
3. **Audit Trail**: System tracks who hid knowledge bases and when
4. **No Data Loss**: Hiding doesn't delete data, just controls visibility
5. **Reversible**: Knowledge bases can be unhidden at any time

### Best Practices

1. **Document Hidden Stores**: Maintain a list of hidden knowledge bases and why they're hidden
2. **Regular Audits**: Periodically review analytics visibility settings
3. **User Communication**: Inform users if their analytics are disabled
4. **Access Logs**: Monitor the analytics_access_log table for suspicious activity
5. **Principle of Least Privilege**: Only enable analytics when necessary

---

## Troubleshooting

### Issue: Analytics Still Visible After Disabling

**Solution**: Check that the user isn't an admin. Admins can always see all analytics.

```sql
SELECT id, email, role, analytics_visible
FROM user_profiles
WHERE email = 'user@example.com';
```

### Issue: Hidden Knowledge Base Appears in Listing

**Solution**: Verify the `is_visible` flag was properly set:

```sql
SELECT id, store_name, is_visible, hidden_by, hidden_at
FROM user_vector_stores
WHERE id = 'store-uuid';
```

If `is_visible = true`, hide it again:

```sql
SELECT hide_knowledge_base('store-uuid', 'admin-uuid');
```

### Issue: Database Functions Not Found

**Solution**: Ensure the migration was run completely:

```sql
-- Check if functions exist
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'enable_user_analytics',
    'disable_user_analytics',
    'hide_knowledge_base',
    'show_knowledge_base'
  );
```

If missing, re-run the migration.

---

## Summary

These visibility control features provide:

- **Privacy**: Analytics hidden by default
- **Control**: Granular admin control over visibility
- **Flexibility**: Knowledge bases can be hidden but still functional
- **Auditability**: Complete tracking of visibility changes
- **Security**: Role-based access with proper validation

For questions or issues, refer to the API reference or contact the development team.
