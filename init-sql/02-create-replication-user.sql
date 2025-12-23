-- PostgreSQL Replication User Setup
-- Creates user for streaming replication to read replica
-- Created: 2025-12-23

-- ============================================
-- Create Replication User
-- ============================================
-- This user is used by the read replica to connect and stream WAL
CREATE USER replication_user WITH REPLICATION ENCRYPTED PASSWORD 'change_me';

-- Grant necessary permissions for replication
GRANT CONNECT ON DATABASE yukyu TO replication_user;

-- ============================================
-- Configure Host-based Authentication (pg_hba.conf alternative)
-- Note: These settings should also be in docker-entrypoint-initdb.d
-- or configured in postgres-primary service environment
-- ============================================
-- Format: TYPE  DATABASE  USER  ADDRESS  METHOD
-- host  replication  replication_user  172.25.0.0/16  trust

-- ============================================
-- Verify Replication Setup
-- ============================================
-- Run these commands to verify replication is working:
--
-- 1. Check replication user exists:
--    SELECT * FROM pg_roles WHERE rolname = 'replication_user';
--
-- 2. Check replication slots:
--    SELECT * FROM pg_replication_slots;
--
-- 3. Check wal sender processes:
--    SELECT * FROM pg_stat_activity WHERE backend_type = 'walsender';
--
-- 4. On replica, check recovery status:
--    SELECT pg_is_in_recovery();
--
-- 5. Monitor replication lag on primary:
--    SELECT slot_name, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;

COMMIT;
