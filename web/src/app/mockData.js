export const INITIAL_SERVERS = [
  { name: "dev-vps", host: "127.0.0.1", user: "root", port: 2222, status: "online", provider: "local-sim" },
  { name: "staging-server", host: "192.168.1.45", user: "ubuntu", port: 22, status: "online", provider: "aws" },
  { name: "prod-db-replica", host: "10.0.4.12", user: "admin", port: 22, status: "offline", provider: "gcp" }
];

export const INITIAL_SETTINGS = [
  { server_name: null, key: "ai_model", value: "claude-3-5-sonnet-20241022" },
  { server_name: null, key: "theme", value: "dark" },
  { server_name: null, key: "log_color", value: "#00ffcc" }, // Neon Teal default
  { server_name: "dev-vps", key: "log_color", value: "#ff007f" }, // Cyan/pink overriding
  { server_name: null, key: "preferred_web_server", value: "nginx" },
  { server_name: null, key: "preferred_editor", value: "vim" }
];

export const INITIAL_AI_MEMORY = [
  { id: 1, server_name: "dev-vps", key: "node_version", value: "v18.16.0", source: "ai_inferred", updated_at: "2026-06-14T12:34:00Z" },
  { id: 2, server_name: "dev-vps", key: "active_db", value: "PostgreSQL 14 on port 5432", source: "ai_inferred", updated_at: "2026-06-14T14:12:00Z" },
  { id: 3, server_name: "dev-vps", key: "main_app_path", value: "/var/www/qwerty-app", source: "user_set", updated_at: "2026-06-14T15:20:00Z" },
  { id: 4, server_name: "staging-server", key: "docker_installed", value: "Docker v24.0.2", source: "ai_inferred", updated_at: "2026-06-14T10:05:00Z" },
  { id: 5, server_name: "staging-server", key: "ssl_expiry", value: "2026-09-01 (Let's Encrypt)", source: "ai_inferred", updated_at: "2026-06-14T11:00:00Z" }
];

export const INITIAL_SESSIONS = [
  { id: 1, server_name: "dev-vps", host: "127.0.0.1", user: "root", started_at: "2026-06-14T18:00:00Z", ended_at: "2026-06-14T18:20:00Z", mode: "standard", command_count: 4, notes: "Routine health check and OS version verification." },
  { id: 2, server_name: "dev-vps", host: "127.0.0.1", user: "root", started_at: "2026-06-14T18:22:00Z", ended_at: null, mode: "agent", command_count: 3, notes: "Automated service audit and resource query." },
  { id: 3, server_name: "staging-server", host: "192.168.1.45", user: "ubuntu", started_at: "2026-06-14T16:30:00Z", ended_at: "2026-06-14T17:15:00Z", mode: "agent", command_count: 5, notes: "SSL status verification and memory inspection." }
];

export const INITIAL_COMMANDS = [
  // Session 1 Commands
  {
    id: 1,
    session_id: 1,
    server_name: "dev-vps",
    command: "cat /etc/os-release",
    description: "Display OS release details",
    output: `PRETTY_NAME="Ubuntu 22.04.5 LTS"\nNAME="Ubuntu"\nVERSION_ID="22.04"\nVERSION="22.04.5 LTS (Jammy Jellyfish)"\nVERSION_CODENAME=jammy\nID=ubuntu`,
    exit_code: 0,
    duration_ms: 120,
    ran_at: "2026-06-14T18:01:00Z",
    was_dry_run: false,
    user_prompt: "Check what OS we are running"
  },
  {
    id: 2,
    session_id: 1,
    server_name: "dev-vps",
    command: "free -h",
    description: "Display memory statistics",
    output: `               total        used        free      shared  buff/cache   available\nMem:           3.8Gi       1.2Gi       1.1Gi        80Mi       1.5Gi       2.3Gi\nSwap:          1.0Gi          0B       1.0Gi`,
    exit_code: 0,
    duration_ms: 85,
    ran_at: "2026-06-14T18:05:00Z",
    was_dry_run: false,
    user_prompt: "how much RAM do we have?"
  },
  {
    id: 3,
    session_id: 1,
    server_name: "dev-vps",
    command: "df -h /",
    description: "Display root filesystem disk space",
    output: `Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        40G   18G   22G  45% /`,
    exit_code: 0,
    duration_ms: 90,
    ran_at: "2026-06-14T18:10:00Z",
    was_dry_run: false,
    user_prompt: "how much disk space is left?"
  },
  {
    id: 4,
    session_id: 1,
    server_name: "dev-vps",
    command: "docker ps",
    description: "List running docker containers",
    output: `CONTAINER ID   IMAGE         COMMAND                  CREATED        STATUS        PORTS                    NAMES\n7c1b52a1d2e3   postgres:14   "docker-entrypoint.s…"   3 days ago     Up 3 days     0.0.0.0:5432->5432/tcp   postgres-db`,
    exit_code: 0,
    duration_ms: 220,
    ran_at: "2026-06-14T18:15:00Z",
    was_dry_run: false,
    user_prompt: "are there any database containers running?"
  },

  // Session 2 Commands (Current Active Session)
  {
    id: 5,
    session_id: 2,
    server_name: "dev-vps",
    command: "systemctl status nginx",
    description: "Get Nginx status details",
    output: `● nginx.service - A high performance web server and a reverse proxy server\n   Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)\n   Active: active (running) since Fri 2026-06-12 10:00:23 UTC; 2 days ago\n Main PID: 9283 (nginx)\n    Tasks: 2 (limit: 4660)\n   Memory: 8.4M\n   CGroup: /system.slice/nginx.service\n           ├─9283 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;\n           └─9284 nginx: worker process`,
    exit_code: 0,
    duration_ms: 140,
    ran_at: "2026-06-14T18:23:00Z",
    was_dry_run: false,
    user_prompt: "is nginx online?"
  },
  {
    id: 6,
    session_id: 2,
    server_name: "dev-vps",
    command: "netstat -tulpn",
    description: "Scan active listening network sockets",
    output: `Active Internet connections (only servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    \ntcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      9283/nginx: master  \ntcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      811/sshd: default   \ntcp        0      0 0.0.0.0:5432            0.0.0.0:*               LISTEN      7c1b52a1d2e3/docker `,
    exit_code: 0,
    duration_ms: 190,
    ran_at: "2026-06-14T18:24:00Z",
    was_dry_run: false,
    user_prompt: "Check what ports are open"
  },
  {
    id: 7,
    session_id: 2,
    server_name: "dev-vps",
    command: "tail -n 20 /var/log/nginx/error.log",
    description: "Examine nginx error log tail",
    output: `2026/06/14 18:00:01 [info] 9284#9284: *120 client closed connection while waiting for request\n2026/06/14 18:20:45 [error] 9284#9284: *145 open() "/var/www/html/favicon.ico" failed (2: No such file or directory)`,
    exit_code: 0,
    duration_ms: 110,
    ran_at: "2026-06-14T18:26:00Z",
    was_dry_run: false,
    user_prompt: "are there any errors in the web server logs?"
  },

  // Session 3 Commands (Staging Server)
  {
    id: 8,
    session_id: 3,
    server_name: "staging-server",
    command: "docker --version",
    description: "Check Docker version",
    output: "Docker version 24.0.2, build cb74dfb",
    exit_code: 0,
    duration_ms: 70,
    ran_at: "2026-06-14T16:35:00Z",
    was_dry_run: false,
    user_prompt: "check if docker is installed"
  },
  {
    id: 9,
    session_id: 3,
    server_name: "staging-server",
    command: "openssl x509 -enddate -noout -in /etc/letsencrypt/live/staging.website.com/fullchain.pem",
    description: "Query certificate expiration date",
    output: "notAfter=Sep  1 12:00:00 2026 GMT",
    exit_code: 0,
    duration_ms: 150,
    ran_at: "2026-06-14T16:42:00Z",
    was_dry_run: false,
    user_prompt: "Check staging SSL certificate expiration"
  }
];

export const INITIAL_SNAPSHOTS = [
  {
    id: 1,
    server_name: "dev-vps",
    captured_at: "2026-06-14T12:00:00Z",
    os_info: "Ubuntu 22.04.5 LTS (5.15.0-88-generic)",
    memory_total_mb: 4096,
    memory_used_mb: 1840,
    disk_total_gb: 40.0,
    disk_used_gb: 15.4,
    cpu_count: 2,
    load_avg: JSON.stringify([0.15, 0.22, 0.18]),
    running_services: JSON.stringify(["sshd", "docker", "nginx", "cron"]),
    open_ports: JSON.stringify([22, 80, 5432]),
    raw_context: "Baseline daily snapshot."
  },
  {
    id: 2,
    server_name: "dev-vps",
    captured_at: "2026-06-14T18:00:00Z",
    os_info: "Ubuntu 22.04.5 LTS (5.15.0-88-generic)",
    memory_total_mb: 4096,
    memory_used_mb: 2310, // increased memory
    disk_total_gb: 40.0,
    disk_used_gb: 18.0, // increased disk
    cpu_count: 2,
    load_avg: JSON.stringify([0.85, 0.60, 0.45]), // increased load
    running_services: JSON.stringify(["sshd", "docker", "nginx", "cron", "redis-server"]), // new service
    open_ports: JSON.stringify([22, 80, 5432, 6379]), // new port 6379
    raw_context: "Active work session snapshot."
  },
  {
    id: 3,
    server_name: "staging-server",
    captured_at: "2026-06-14T17:00:00Z",
    os_info: "Ubuntu 20.04.6 LTS (5.4.0-150-generic)",
    memory_total_mb: 8192,
    memory_used_mb: 3120,
    disk_total_gb: 80.0,
    disk_used_gb: 45.2,
    cpu_count: 4,
    load_avg: JSON.stringify([0.05, 0.12, 0.10]),
    running_services: JSON.stringify(["sshd", "docker", "fail2ban"]),
    open_ports: JSON.stringify([22, 443, 80]),
    raw_context: "Standard staging baseline snapshot."
  }
];
