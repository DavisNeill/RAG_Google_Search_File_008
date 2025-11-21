# Visibility Features - Quick Reference Guide

## 🔒 Analytics Visibility Control

### Enable Analytics for User
```bash
POST /api/admin/analytics/enable/<user_id>
```

### Disable Analytics for User
```bash
POST /api/admin/analytics/disable/<user_id>
```

### Bulk Enable Analytics
```bash
POST /api/admin/analytics/bulk-enable
Body: { "user_ids": ["uuid1", "uuid2"] }
```

### Bulk Disable Analytics
```bash
POST /api/admin/analytics/bulk-disable
Body: { "user_ids": ["uuid1", "uuid2"] }
```

### Check User Status
```bash
GET /api/admin/analytics/status/<user_id>
```

### List All Users
```bash
GET /api/admin/users/list
```

---

## 📚 Knowledge Base Visibility Control

### Hide Knowledge Base
```bash
POST /api/admin/knowledge-base/hide/<store_id>
```

### Show Knowledge Base
```bash
POST /api/admin/knowledge-base/show/<store_id>
```

### Bulk Hide
```bash
POST /api/admin/knowledge-base/bulk-hide
Body: { "store_ids": ["uuid1", "uuid2"] }
```

### Bulk Show
```bash
POST /api/admin/knowledge-base/bulk-show
Body: { "store_ids": ["uuid1", "uuid2"] }
```

### Get All (Admin)
```bash
GET /api/admin/knowledge-base/all
```

### Get Visible (User)
```bash
GET /api/knowledge-base/visible
```

---

## 📊 Key Database Functions

### Analytics Functions
```sql
-- Enable analytics
SELECT enable_user_analytics('user-uuid', 'admin-uuid');

-- Disable analytics
SELECT disable_user_analytics('user-uuid', 'admin-uuid');

-- Bulk enable
SELECT bulk_enable_analytics(ARRAY['user1-uuid', 'user2-uuid'], 'admin-uuid');

-- Bulk disable
SELECT bulk_disable_analytics(ARRAY['user1-uuid', 'user2-uuid'], 'admin-uuid');

-- Check permission
SELECT can_view_analytics('target-user-uuid', 'requesting-user-uuid');
```

### Knowledge Base Functions
```sql
-- Hide knowledge base
SELECT hide_knowledge_base('store-uuid', 'admin-uuid');

-- Show knowledge base
SELECT show_knowledge_base('store-uuid', 'admin-uuid');

-- Bulk hide
SELECT bulk_hide_knowledge_bases(ARRAY['store1-uuid', 'store2-uuid'], 'admin-uuid');

-- Bulk show
SELECT bulk_show_knowledge_bases(ARRAY['store1-uuid', 'store2-uuid'], 'admin-uuid');

-- Get visible stores
SELECT * FROM get_visible_knowledge_bases();

-- Get all stores (admin)
SELECT * FROM get_all_knowledge_bases('admin-uuid');
```

---

## 🔍 Quick Queries

### Check Analytics Status
```sql
SELECT id, email, role, analytics_visible,
       analytics_visibility_updated_by,
       analytics_visibility_updated_at
FROM user_profiles
WHERE email = 'user@example.com';
```

### Check Knowledge Base Visibility
```sql
SELECT id, store_name, store_id, is_visible,
       hidden_by, hidden_at
FROM user_vector_stores
ORDER BY created_at DESC;
```

### Find Users with Disabled Analytics
```sql
SELECT id, email, created_at
FROM user_profiles
WHERE analytics_visible = false
  AND role = 'user';
```

### Find Hidden Knowledge Bases
```sql
SELECT id, store_name, description,
       hidden_by, hidden_at
FROM user_vector_stores
WHERE is_visible = false;
```

---

## ⚡ Common Operations

### 1. Enable Analytics for New User
```bash
# Get user ID from login
curl -X POST http://localhost:5000/api/admin/analytics/enable/<user-id>
```

### 2. Hide Confidential Knowledge Base
```bash
# Get store ID from list
curl -X POST http://localhost:5000/api/admin/knowledge-base/hide/<store-id>
```

### 3. Bulk Enable Analytics for Multiple Users
```bash
curl -X POST http://localhost:5000/api/admin/analytics/bulk-enable \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["uuid1", "uuid2", "uuid3"]}'
```

### 4. View All Hidden Knowledge Bases (Admin)
```bash
curl http://localhost:5000/api/admin/knowledge-base/all | jq '.stores[] | select(.is_visible == false)'
```

---

## 🚨 Important Notes

### Analytics Visibility
- ✅ **Default**: Disabled for all new users
- ✅ **Who Can Enable**: Admins only
- ✅ **Who Can View**: User (if enabled) OR admins
- ⚠️ Endpoints affected: `/api/memory/analytics`, `/api/memory/export`

### Knowledge Base Visibility
- ✅ **Default**: Visible for all new stores
- ✅ **Who Can Hide**: Admins only
- ✅ **Who Can See Hidden**: Admins in listings
- ⚠️ **Important**: Hidden stores are still queryable if store ID is known
- ⚠️ Endpoints affected: `/stores`, `/api/knowledge-base/visible`

---

## 🛠️ Setup Checklist

- [ ] Run `database_schema_visibility_features.sql` in Supabase
- [ ] Verify new columns exist in tables
- [ ] Test admin endpoints with admin account
- [ ] Test user access with regular account
- [ ] Review default analytics visibility (should be false)
- [ ] Document hidden knowledge bases

---

## 📞 Troubleshooting

**Problem**: User can't see analytics even when enabled
- Check: `SELECT analytics_visible FROM user_profiles WHERE id = 'user-uuid';`
- Solution: Ensure `analytics_visible = true`

**Problem**: Hidden knowledge base still appears
- Check: `SELECT is_visible FROM user_vector_stores WHERE id = 'store-uuid';`
- Solution: Ensure `is_visible = false` and user is not admin

**Problem**: Database functions not found
- Check: `SELECT routine_name FROM information_schema.routines WHERE routine_name LIKE '%analytics%';`
- Solution: Re-run migration SQL

---

## 📚 Full Documentation

For complete details, examples, and security considerations, see:
- `VISIBILITY_FEATURES.md` - Full documentation
- `database_schema_visibility_features.sql` - Database schema

---

*Last Updated: January 2025*
