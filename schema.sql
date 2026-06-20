-- PostgreSQL / Supabase Schema Migration Script
-- Enable pgvector if needed for future semantic search upgrades
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Table: sessions
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    host TEXT NOT NULL,
    "user" TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    mode TEXT NOT NULL,
    command_count INTEGER DEFAULT 0,
    notes TEXT,
    summary TEXT
);

-- 2. Table: commands
CREATE TABLE IF NOT EXISTS commands (
    id SERIAL PRIMARY KEY,
    session_id INTEGER,
    server_name TEXT NOT NULL,
    command TEXT NOT NULL,
    description TEXT,
    output TEXT,
    exit_code INTEGER,
    duration_ms INTEGER,
    ran_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    was_dry_run BOOLEAN DEFAULT FALSE,
    user_prompt TEXT
);

-- 3. Table: ai_memory
CREATE TABLE IF NOT EXISTS ai_memory (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT DEFAULT 'ai_inferred',
    category TEXT,
    confidence REAL DEFAULT 0.8,
    times_accessed INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    CONSTRAINT unique_server_key UNIQUE (server_name, key)
);

-- 4. Table: settings
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    server_name TEXT, -- NULL = global setting
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_server_setting UNIQUE (server_name, key)
);

-- 5. Table: server_snapshots
CREATE TABLE IF NOT EXISTS server_snapshots (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    os_info TEXT,
    memory_total_mb INTEGER,
    memory_used_mb INTEGER,
    disk_total_gb REAL,
    disk_used_gb REAL,
    cpu_count INTEGER,
    load_avg TEXT,
    running_services TEXT,
    open_ports TEXT,
    raw_context TEXT
);

-- 6. Table: projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT,
    type TEXT,
    process_manager TEXT,
    process_name TEXT,
    port INTEGER,
    domain TEXT,
    runtime_version TEXT,
    package_manager TEXT,
    git_remote TEXT,
    git_branch TEXT,
    last_deploy_at TIMESTAMPTZ,
    brain_file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_server_project UNIQUE (server_name, name)
);

-- 7. Table: tracked_files
CREATE TABLE IF NOT EXISTS tracked_files (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    project_name TEXT,
    path TEXT NOT NULL,
    category TEXT,
    content_hash TEXT,
    content_snapshot TEXT,
    last_read_at TIMESTAMPTZ,
    last_modified_at TIMESTAMPTZ,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_server_file UNIQUE (server_name, path)
);

-- 8. Table: file_versions
CREATE TABLE IF NOT EXISTS file_versions (
    id SERIAL PRIMARY KEY,
    tracked_file_id INTEGER NOT NULL,
    session_id INTEGER,
    server_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    version_number INTEGER DEFAULT 1,
    content_before TEXT,
    content_after TEXT,
    diff TEXT,
    change_reason TEXT,
    user_prompt TEXT,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reverted_at TIMESTAMPTZ
);

-- 9. Table: brain_versions
CREATE TABLE IF NOT EXISTS brain_versions (
    id SERIAL PRIMARY KEY,
    server_name TEXT NOT NULL,
    project_name TEXT, -- NULL = SERVER.md
    version_number INTEGER DEFAULT 1,
    trigger TEXT DEFAULT 'sync',
    content TEXT NOT NULL,
    summary_of_changes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
