-- Enhanced Database Schema for Visibility Features
-- Run this SQL in your Supabase SQL Editor to add visibility controls
-- This extends the existing admin schema with new features

-- ============================================================================
-- FEATURE 1: User Analytics Visibility Control (Hidden by Default)
-- ============================================================================

-- Add analytics visibility column to user_profiles
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS analytics_visible BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS analytics_visibility_updated_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS analytics_visibility_updated_at TIMESTAMP WITH TIME ZONE;

-- Create index for analytics visibility
CREATE INDEX IF NOT EXISTS idx_user_profiles_analytics_visible ON user_profiles(analytics_visible);

-- ============================================================================
-- FEATURE 2: Knowledge Base Visibility Control (Hidden from List, Still Queryable)
-- ============================================================================

-- Add visibility columns to user_vector_stores
ALTER TABLE user_vector_stores
ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS hidden_by UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS hidden_at TIMESTAMP WITH TIME ZONE;

-- Create index for store visibility
CREATE INDEX IF NOT EXISTS idx_user_vector_stores_visible ON user_vector_stores(is_visible);

-- ============================================================================
-- ADMIN FUNCTIONS: Analytics Visibility Control
-- ============================================================================

-- Function to enable analytics for a user
CREATE OR REPLACE FUNCTION enable_user_analytics(target_user_id UUID, admin_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_profiles
        SET analytics_visible = true,
            analytics_visibility_updated_by = admin_id,
            analytics_visibility_updated_at = NOW()
        WHERE id = target_user_id;
        RETURN true;
    END IF;
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to disable analytics for a user
CREATE OR REPLACE FUNCTION disable_user_analytics(target_user_id UUID, admin_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_profiles
        SET analytics_visible = false,
            analytics_visibility_updated_by = admin_id,
            analytics_visibility_updated_at = NOW()
        WHERE id = target_user_id;
        RETURN true;
    END IF;
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to bulk enable analytics
CREATE OR REPLACE FUNCTION bulk_enable_analytics(user_ids UUID[], admin_id UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_profiles
        SET analytics_visible = true,
            analytics_visibility_updated_by = admin_id,
            analytics_visibility_updated_at = NOW()
        WHERE id = ANY(user_ids);
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RETURN updated_count;
    END IF;
    RETURN 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to bulk disable analytics
CREATE OR REPLACE FUNCTION bulk_disable_analytics(user_ids UUID[], admin_id UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_profiles
        SET analytics_visible = false,
            analytics_visibility_updated_by = admin_id,
            analytics_visibility_updated_at = NOW()
        WHERE id = ANY(user_ids);
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RETURN updated_count;
    END IF;
    RETURN 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ADMIN FUNCTIONS: Knowledge Base Visibility Control
-- ============================================================================

-- Function to hide knowledge base (store)
CREATE OR REPLACE FUNCTION hide_knowledge_base(store_id_param UUID, admin_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_vector_stores
        SET is_visible = false,
            hidden_by = admin_id,
            hidden_at = NOW()
        WHERE id = store_id_param;
        RETURN true;
    END IF;
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to show knowledge base (store)
CREATE OR REPLACE FUNCTION show_knowledge_base(store_id_param UUID, admin_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_vector_stores
        SET is_visible = true,
            hidden_by = NULL,
            hidden_at = NULL
        WHERE id = store_id_param;
        RETURN true;
    END IF;
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to bulk hide knowledge bases
CREATE OR REPLACE FUNCTION bulk_hide_knowledge_bases(store_ids UUID[], admin_id UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_vector_stores
        SET is_visible = false,
            hidden_by = admin_id,
            hidden_at = NOW()
        WHERE id = ANY(store_ids);
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RETURN updated_count;
    END IF;
    RETURN 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to bulk show knowledge bases
CREATE OR REPLACE FUNCTION bulk_show_knowledge_bases(store_ids UUID[], admin_id UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    IF is_admin(admin_id) THEN
        UPDATE user_vector_stores
        SET is_visible = true,
            hidden_by = NULL,
            hidden_at = NULL
        WHERE id = ANY(store_ids);
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RETURN updated_count;
    END IF;
    RETURN 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- HELPER FUNCTIONS: Check Visibility Permissions
-- ============================================================================

-- Check if user can view analytics (user themselves OR admin)
CREATE OR REPLACE FUNCTION can_view_analytics(target_user_id UUID, requesting_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- User can always view their own analytics if enabled
    IF target_user_id = requesting_user_id THEN
        RETURN (SELECT analytics_visible FROM user_profiles WHERE id = target_user_id);
    END IF;

    -- Admins can view all analytics
    RETURN is_admin(requesting_user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get all visible knowledge bases for listing
CREATE OR REPLACE FUNCTION get_visible_knowledge_bases()
RETURNS SETOF user_vector_stores AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM user_vector_stores
    WHERE is_visible = true
    ORDER BY created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get all knowledge bases (admin only)
CREATE OR REPLACE FUNCTION get_all_knowledge_bases(admin_id UUID)
RETURNS SETOF user_vector_stores AS $$
BEGIN
    IF is_admin(admin_id) THEN
        RETURN QUERY
        SELECT * FROM user_vector_stores
        ORDER BY created_at DESC;
    END IF;
    RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ANALYTICS TRACKING TABLE (Optional - for future use)
-- ============================================================================

-- Table to track when users access analytics
CREATE TABLE IF NOT EXISTS analytics_access_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    accessed_by UUID NOT NULL REFERENCES auth.users(id),
    access_type TEXT CHECK (access_type IN ('view', 'export', 'search')),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on analytics_access_log
ALTER TABLE analytics_access_log ENABLE ROW LEVEL SECURITY;

-- Only admins can view access logs
CREATE POLICY "Admins can view analytics access logs"
    ON analytics_access_log FOR SELECT
    USING (is_admin(auth.uid()));

-- Create index for analytics access log
CREATE INDEX IF NOT EXISTS idx_analytics_access_log_user_id ON analytics_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_access_log_accessed_at ON analytics_access_log(accessed_at);

-- ============================================================================
-- SUMMARY OF NEW FEATURES
-- ============================================================================

-- FEATURE 1: User Analytics Visibility Control
-- ✅ Analytics are hidden by default (analytics_visible = false)
-- ✅ Admins can enable/disable analytics for individual users
-- ✅ Admins can bulk enable/disable analytics
-- ✅ Users can only see their own analytics if enabled
-- ✅ Admins can always see all analytics
-- ✅ Tracks who changed visibility and when

-- FEATURE 2: Knowledge Base Visibility Control
-- ✅ Knowledge bases can be hidden from lists
-- ✅ Hidden knowledge bases are still queryable (not deleted)
-- ✅ Admins can hide/show individual knowledge bases
-- ✅ Admins can bulk hide/show knowledge bases
-- ✅ Regular users only see visible knowledge bases in lists
-- ✅ Tracks who hid the knowledge base and when

-- USAGE EXAMPLES:
-- 1. Enable analytics for a user:
--    SELECT enable_user_analytics('user-uuid', 'admin-uuid');
--
-- 2. Hide a knowledge base:
--    SELECT hide_knowledge_base('store-uuid', 'admin-uuid');
--
-- 3. Get visible knowledge bases:
--    SELECT * FROM get_visible_knowledge_bases();
--
-- 4. Bulk disable analytics:
--    SELECT bulk_disable_analytics(ARRAY['user1-uuid', 'user2-uuid'], 'admin-uuid');
