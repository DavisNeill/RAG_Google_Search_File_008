-- Database Schema for System Improvements
-- Run this SQL in your Supabase SQL Editor
-- Includes: Usage Quotas and Document Versioning

-- ============================================================================
-- TIER 2: Usage Quotas System
-- ============================================================================

-- Table to track daily usage
CREATE TABLE IF NOT EXISTS user_usage_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    queries_count INTEGER DEFAULT 0,
    uploads_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Create indexes for usage tracking
CREATE INDEX IF NOT EXISTS idx_user_usage_tracking_user_id ON user_usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_tracking_date ON user_usage_tracking(date);

-- Enable RLS
ALTER TABLE user_usage_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can view their own usage
CREATE POLICY "Users can view own usage"
    ON user_usage_tracking FOR SELECT
    USING (auth.uid() = user_id);

-- Admins can view all usage
CREATE POLICY "Admins can view all usage"
    ON user_usage_tracking FOR SELECT
    USING (is_admin(auth.uid()));

-- Function to get queries count for a user on a specific date
CREATE OR REPLACE FUNCTION get_user_queries_count(p_user_id UUID, p_date DATE)
RETURNS INTEGER AS $$
DECLARE
    query_count INTEGER;
BEGIN
    SELECT queries_count INTO query_count
    FROM user_usage_tracking
    WHERE user_id = p_user_id AND date = p_date;

    RETURN COALESCE(query_count, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get uploads count for a user on a specific date
CREATE OR REPLACE FUNCTION get_user_uploads_count(p_user_id UUID, p_date DATE)
RETURNS INTEGER AS $$
DECLARE
    upload_count INTEGER;
BEGIN
    SELECT uploads_count INTO upload_count
    FROM user_usage_tracking
    WHERE user_id = p_user_id AND date = p_date;

    RETURN COALESCE(upload_count, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get storage usage for a user
CREATE OR REPLACE FUNCTION get_user_storage_usage(p_user_id UUID)
RETURNS BIGINT AS $$
DECLARE
    total_size BIGINT;
BEGIN
    SELECT COALESCE(SUM(file_size), 0) INTO total_size
    FROM user_documents
    WHERE user_id = p_user_id;

    RETURN total_size;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment query count
CREATE OR REPLACE FUNCTION increment_query_count(p_user_id UUID, p_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_usage_tracking (user_id, date, queries_count)
    VALUES (p_user_id, CURRENT_DATE, p_count)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        queries_count = user_usage_tracking.queries_count + p_count,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment upload count
CREATE OR REPLACE FUNCTION increment_upload_count(p_user_id UUID, p_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_usage_tracking (user_id, date, uploads_count)
    VALUES (p_user_id, CURRENT_DATE, p_count)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        uploads_count = user_usage_tracking.uploads_count + p_count,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TIER 3: Document Versioning System
-- ============================================================================

-- Table to store document versions
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES user_documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT,  -- SHA256 hash for deduplication
    mime_type TEXT,
    uploaded_by UUID NOT NULL REFERENCES auth.users(id),
    version_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, version_number)
);

-- Create indexes for document versions
CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON document_versions(created_at);

-- Enable RLS
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Admins can manage versions
CREATE POLICY "Admins can view all versions"
    ON document_versions FOR SELECT
    USING (is_admin(auth.uid()));

CREATE POLICY "Admins can insert versions"
    ON document_versions FOR INSERT
    WITH CHECK (is_admin(auth.uid()));

CREATE POLICY "Admins can delete versions"
    ON document_versions FOR DELETE
    USING (is_admin(auth.uid()));

-- Function to create a new document version
CREATE OR REPLACE FUNCTION create_document_version(
    p_document_id UUID,
    p_file_name TEXT,
    p_file_path TEXT,
    p_file_size BIGINT,
    p_file_hash TEXT,
    p_mime_type TEXT,
    p_uploaded_by UUID,
    p_version_notes TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    next_version INTEGER;
    version_id UUID;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version_number), 0) + 1 INTO next_version
    FROM document_versions
    WHERE document_id = p_document_id;

    -- Create version
    INSERT INTO document_versions (
        document_id, version_number, file_name, file_path,
        file_size, file_hash, mime_type, uploaded_by, version_notes
    )
    VALUES (
        p_document_id, next_version, p_file_name, p_file_path,
        p_file_size, p_file_hash, p_mime_type, p_uploaded_by, p_version_notes
    )
    RETURNING id INTO version_id;

    RETURN version_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get document versions
CREATE OR REPLACE FUNCTION get_document_versions(p_document_id UUID)
RETURNS TABLE (
    id UUID,
    version_number INTEGER,
    file_name TEXT,
    file_size BIGINT,
    mime_type TEXT,
    uploaded_by UUID,
    version_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dv.id,
        dv.version_number,
        dv.file_name,
        dv.file_size,
        dv.mime_type,
        dv.uploaded_by,
        dv.version_notes,
        dv.created_at
    FROM document_versions dv
    WHERE dv.document_id = p_document_id
    ORDER BY dv.version_number DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to restore document version
CREATE OR REPLACE FUNCTION restore_document_version(
    p_version_id UUID,
    p_admin_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    version_record RECORD;
BEGIN
    IF NOT is_admin(p_admin_id) THEN
        RETURN false;
    END IF;

    -- Get version details
    SELECT * INTO version_record
    FROM document_versions
    WHERE id = p_version_id;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Update main document with version data
    UPDATE user_documents
    SET
        file_name = version_record.file_name,
        file_path = version_record.file_path,
        file_size = version_record.file_size,
        mime_type = version_record.mime_type
    WHERE id = version_record.document_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup old versions (keep only N most recent)
CREATE OR REPLACE FUNCTION cleanup_old_versions(
    p_document_id UUID,
    p_keep_count INTEGER DEFAULT 10
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM document_versions
    WHERE id IN (
        SELECT id
        FROM document_versions
        WHERE document_id = p_document_id
        ORDER BY version_number DESC
        OFFSET p_keep_count
    );

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- AUTO-CLEANUP: Remove old usage tracking data
-- ============================================================================

-- Function to cleanup old usage data (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_usage_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_usage_tracking
    WHERE date < CURRENT_DATE - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ADMIN FUNCTIONS: Usage Analytics
-- ============================================================================

-- Function to get usage statistics across all users
CREATE OR REPLACE FUNCTION get_usage_statistics(admin_id UUID)
RETURNS TABLE (
    total_users INTEGER,
    active_users_today INTEGER,
    total_queries_today INTEGER,
    total_uploads_today INTEGER,
    avg_queries_per_user NUMERIC,
    avg_uploads_per_user NUMERIC
) AS $$
BEGIN
    IF NOT is_admin(admin_id) THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        (SELECT COUNT(DISTINCT user_id) FROM user_profiles)::INTEGER,
        (SELECT COUNT(DISTINCT user_id) FROM user_usage_tracking WHERE date = CURRENT_DATE)::INTEGER,
        (SELECT COALESCE(SUM(queries_count), 0) FROM user_usage_tracking WHERE date = CURRENT_DATE)::INTEGER,
        (SELECT COALESCE(SUM(uploads_count), 0) FROM user_usage_tracking WHERE date = CURRENT_DATE)::INTEGER,
        (SELECT COALESCE(AVG(queries_count), 0) FROM user_usage_tracking WHERE date = CURRENT_DATE),
        (SELECT COALESCE(AVG(uploads_count), 0) FROM user_usage_tracking WHERE date = CURRENT_DATE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SUMMARY
-- ============================================================================

-- Usage Quotas:
-- ✅ Tracks queries and uploads per day per user
-- ✅ Calculates storage usage
-- ✅ Functions to check and increment usage
-- ✅ Automatic cleanup of old data

-- Document Versioning:
-- ✅ Stores complete version history
-- ✅ Track who uploaded each version
-- ✅ Restore previous versions
-- ✅ Automatic cleanup of old versions
-- ✅ File hash for deduplication

-- Usage Examples:
-- 1. Get user's queries today:
--    SELECT get_user_queries_count('user-uuid', CURRENT_DATE);
--
-- 2. Increment query count:
--    SELECT increment_query_count('user-uuid', 1);
--
-- 3. Create document version:
--    SELECT create_document_version('doc-uuid', 'file.pdf', '/path/to/file', 1024, 'hash', 'application/pdf', 'admin-uuid', 'Initial version');
--
-- 4. Get document versions:
--    SELECT * FROM get_document_versions('doc-uuid');
--
-- 5. Restore version:
--    SELECT restore_document_version('version-uuid', 'admin-uuid');
