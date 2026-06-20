
**vibe-server**

**Memory System & Server Brain**

Engineering Specification for Coding Agent

v1.0 — Versioned Knowledge Graph + /sync System


# **Table of Contents**





# **1. Concept — The Server Brain**
The memory system turns vibe-server from a stateless command runner into a persistent knowledge base about each server. Every file it reads, every config it touches, every project it discovers, every change it makes — all of it is recorded, versioned, and made available to the AI on every future session.

The core metaphor is a GitHub repo for your server's state. Not your code — your infrastructure knowledge. Condensed markdown files that describe what's running, where things live, what's been changed and why. Human-readable. Diffable. Queryable by the AI.

## **1.1 The Three Layers**

|**Layer**|**What it is**|**How it's used**|
| :- | :- | :- |
|Live State|Redis — current session, open files, pending changes|Fast access during active session, cleared on exit|
|Versioned Brain|Postgres — full history of everything ever known|AI context injection, change history, rollback|
|Brain Files|Markdown files per project — condensed knowledge|Human readable, shareable, diffable like git|

## **1.2 Infrastructure Stack**
- **PostgreSQL + pgvector:** primary database for all persistent state. pgvector enables semantic search over memories — the AI can find relevant past knowledge by meaning, not just keyword.
- **Supabase:** hosted Postgres + pgvector + REST API. Free tier sufficient for launch. Gives you auth, realtime, and a dashboard for free.
- **Redis (Upstash):** session state only. Tracks what's open, what's been read this session, pending changes not yet committed. Serverless Redis — pay per request, zero ops.
- **No other services:** resist the urge to add more. Postgres + Redis handles everything described in this spec.


# **2. Data Model**
All tables live in Postgres via Supabase. Use Prisma or SQLAlchemy as the ORM — Prisma preferred if the backend is Node, SQLAlchemy if Python.

## **2.1 Table: servers**
One row per server profile. The root entity everything else hangs off.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|user\_id|UUID FK|Owner — references auth.users|
|name|TEXT|Profile name, e.g. 'prod'|
|host|TEXT|IP or hostname|
|user|TEXT|SSH username|
|port|INTEGER|SSH port, default 22|
|hoster|TEXT|Detected hoster: hetzner/do/aws/vultr etc|
|os\_info|TEXT|OS string captured at first sync|
|last\_synced\_at|TIMESTAMPTZ|When /sync last completed|
|brain\_version|INTEGER|Monotonic version counter for brain files|
|created\_at|TIMESTAMPTZ|First added|

## **2.2 Table: projects**
A project is any discrete application or service discovered on the server. Auto-detected during /sync by finding app directories, process names, and config files.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|server\_id|UUID FK|References servers.id|
|name|TEXT|Project name, e.g. 'api', 'frontend', 'worker'|
|path|TEXT|Absolute path on server, e.g. /var/www/api|
|type|TEXT|node/python/ruby/php/static/docker/unknown|
|process\_manager|TEXT|pm2/systemd/supervisor/docker/none|
|process\_name|TEXT|Name in process manager, e.g. 'api'|
|port|INTEGER|Primary port this project listens on|
|domain|TEXT|Domain name if nginx/caddy config found|
|runtime\_version|TEXT|Node 20.11 / Python 3.11 etc|
|package\_manager|TEXT|npm/yarn/pnpm/pip/poetry|
|deploy\_path|TEXT|Where deploys land, if different from path|
|git\_remote|TEXT|Git remote URL if .git found|
|git\_branch|TEXT|Current branch|
|last\_deploy\_at|TIMESTAMPTZ|Detected from git log or deploy timestamp|
|brain\_file\_path|TEXT|Path to this project's .md brain file|
|created\_at|TIMESTAMPTZ|When first discovered|
|updated\_at|TIMESTAMPTZ|Last update|

## **2.3 Table: tracked\_files**
Every file vibe-server has read or touched. Stores content hash so it knows when something changed externally between sessions.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|server\_id|UUID FK|References servers.id|
|project\_id|UUID FK|References projects.id — nullable|
|path|TEXT|Absolute path on server|
|category|TEXT|nginx/systemd/env/cron/app-config/ssh/docker/other|
|content\_hash|TEXT|SHA256 of file content at last read|
|content\_snapshot|TEXT|Full content at last read — capped 50KB|
|last\_read\_at|TIMESTAMPTZ|When vibe-server last read this file|
|last\_modified\_at|TIMESTAMPTZ|mtime on server at last read|
|is\_sensitive|BOOLEAN|True for .env, keys, passwords — redact in brain files|
|created\_at|TIMESTAMPTZ|When first tracked|

## **2.4 Table: file\_versions**
Every time vibe-server writes to a file, the before and after content is stored here. This is the undo log and audit trail.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|tracked\_file\_id|UUID FK|References tracked\_files.id|
|session\_id|UUID FK|Which session made this change|
|version\_number|INTEGER|Monotonic per file, starts at 1|
|content\_before|TEXT|Full file content before change|
|content\_after|TEXT|Full file content after change|
|diff|TEXT|Unified diff string|
|change\_reason|TEXT|AI-generated one-line description of why|
|user\_prompt|TEXT|The user message that triggered the edit|
|changed\_at|TIMESTAMPTZ|When the write happened|
|reverted\_at|TIMESTAMPTZ|Set if this version was rolled back|

## **2.5 Table: memories**
Structured facts the AI has learned about the server. Each memory has a vector embedding so the AI can retrieve relevant memories by semantic similarity, not just exact key match.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|server\_id|UUID FK|References servers.id|
|project\_id|UUID FK|Project scope — nullable for server-wide memories|
|key|TEXT|Short slug: 'app\_port', 'deploy\_command', 'nginx\_config\_path'|
|value|TEXT|The fact: '3000', 'pm2 reload api', '/etc/nginx/sites-available/api'|
|category|TEXT|config/deployment/incident/preference/discovery|
|confidence|REAL|0\.0-1.0 — AI-assigned confidence in this memory|
|embedding|vector(1536)|OpenAI/Anthropic embedding for semantic search|
|source|TEXT|ai\_inferred/user\_set/sync\_discovered|
|times\_accessed|INTEGER|How often this memory has been retrieved|
|last\_accessed\_at|TIMESTAMPTZ|For LRU eviction of stale memories|
|expires\_at|TIMESTAMPTZ|Optional TTL — null = permanent|
|created\_at|TIMESTAMPTZ|When first recorded|
|updated\_at|TIMESTAMPTZ|Last update|

## **2.6 Table: brain\_versions**
Every time a brain file is regenerated, the previous version is stored here. This is the git-like versioning for the knowledge files.

|**Column**|**Type**|**Description**|
| :- | :- | :- |
|id|UUID PK|Auto-generated UUID|
|server\_id|UUID FK|References servers.id|
|project\_id|UUID FK|References projects.id — null for server brain|
|version\_number|INTEGER|Monotonic counter|
|trigger|TEXT|What caused regeneration: sync/edit/manual|
|content|TEXT|Full markdown content of brain file at this version|
|summary\_of\_changes|TEXT|AI-generated changelog entry|
|created\_at|TIMESTAMPTZ|When this version was written|

## **2.7 Redis Schema (Session State)**
All keys are namespaced by session\_id. TTL = 24 hours. Everything here is ephemeral and rebuilt on reconnect.

|**Key Pattern**|**Type**|**Contains**|
| :- | :- | :- |
|session:{id}:state|Hash|current server, mode, dry\_run, user\_id|
|session:{id}:open\_files|Set|Paths of files read this session|
|session:{id}:pending\_changes|List|JSON of changes not yet committed|
|session:{id}:conversation|List|AI message history for this session|
|session:{id}:command\_buffer|List|Commands run, for context injection|
|server:{id}:sync\_lock|String|Set during /sync to prevent concurrent syncs|
|server:{id}:memory\_cache|Hash|Hot memories for this server, refreshed on connect|


# **3. Brain Files — The Knowledge Markdown**
Brain files are the human-readable layer of the memory system. One markdown file per project, one server-level brain file. Auto-generated and auto-updated. The AI reads them on every session start. Users can read them too — they're the source of truth for what vibe-server knows.

Stored in two places: in Postgres (brain\_versions table, fully versioned) and optionally synced to a local directory the user can push to git.

## **3.1 Server Brain File**
Located at ~/.vibe-server/brains/{server\_name}/SERVER.md

\# SERVER BRAIN — prod

Last synced: 2026-06-14 02:31 UTC | Brain version: 12

\## Identity

\- Host: 167.99.12.44 (Hetzner CX21)

\- OS: Ubuntu 22.04.3 LTS

\- Specs: 2 vCPU, 4GB RAM, 40GB SSD

\- Uptime: 47 days

\## Projects

\- [api] Node.js Express app — /var/www/api — port 3000 — PM2

\- [frontend] Static site — /var/www/frontend — nginx served

\- [worker] Python queue worker — /var/www/worker — systemd

\## Infrastructure

\- Web server: nginx 1.24 — config at /etc/nginx/sites-available/

\- SSL: Let's Encrypt via certbot — expires 2026-08-20

\- Firewall: ufw — ports open: 22, 80, 443

\- Swap: 2GB enabled at /swapfile

\## Known Issues

\- api process restarts ~weekly due to memory growth (possible leak)

\- certbot auto-renew cron confirmed working

\## Change Log

\- 2026-06-14: Raised MemoryLimit to 2GB in api.service [session #47]

\- 2026-06-12: Added rate limiting to nginx for /api routes [session #45]

\- 2026-06-10: Deployed worker service, created systemd unit [session #43]

## **3.2 Project Brain File**
Located at ~/.vibe-server/brains/{server\_name}/{project\_name}.md

\# PROJECT BRAIN — api (prod)

Last updated: 2026-06-14 | Version: 8

\## Location

\- Path: /var/www/api

\- Git remote: git@github.com:user/api.git

\- Branch: main | Last deploy: 2026-06-13 18:22

\## Runtime

\- Node.js v20.11.0 | npm

\- Process manager: PM2 | Process name: api

\- Port: 3000 | Domain: api.myapp.com

\## Key Files

\- Entry: /var/www/api/index.js

\- Config: /var/www/api/.env [sensitive — not shown]

\- PM2: /var/www/api/ecosystem.config.js

\- Nginx: /etc/nginx/sites-available/api

\- Systemd: N/A (PM2 manages this)

\## Deploy Process

cd /var/www/api && git pull && npm install && pm2 reload api

\## Environment (keys only — values redacted)

\- NODE\_ENV, PORT, DATABASE\_URL, REDIS\_URL, JWT\_SECRET

\## Nginx Config Summary

\- Listens on 443 (SSL) + 80 (redirect)

\- Proxies / → 127.0.0.1:3000

\- Rate limit: 10r/s on /api/

\- Gzip enabled

\## Incidents

\- 2026-06-14: OOM crash — MemoryLimit raised in systemd, root cause unclear

\- 2026-06-01: 502 errors — caused by missing node\_modules after git pull

\## Preferences

\- User prefers: check logs before restart, use pm2 reload not restart

## **3.3 Brain File Generation Rules**
- Never include sensitive values — .env values, passwords, private keys are always redacted
- Always include .env keys so the AI knows what config exists without seeing values
- Incident log: append, never overwrite — it's a history, not a status
- Change log: max 20 entries, oldest roll off
- File is regenerated after every /sync and after any file edit
- Version number increments on every regeneration
- AI reads brain files at session start — loaded as system prompt context


# **4. The /sync System**
/sync is the discovery command. It crawls the server, builds or updates the knowledge graph, and regenerates all brain files. Run it once on a new server, then periodically or after major changes.

## **4.1 /sync Phases**

### **Phase 1 — Server Inventory (always runs)**
- OS, kernel, distro, uptime
- CPU count, total/used RAM, total/used disk per mount
- Open ports: ss -tlnp
- Listening services: systemctl list-units --type=service --state=running
- Installed runtimes: node --version, python3 --version, ruby --version, go version, php --version
- Installed tools: nginx -v, docker --version, pm2 --version, certbot --version
- Firewall rules: ufw status or nftables
- Cron jobs: crontab -l for root and common users
- Writes snapshot row to server\_snapshots, updates servers.last\_synced\_at

### **Phase 2 — Project Discovery**
- Scan common web roots: /var/www/, /home/\*/\*, /opt/\*, /srv/\*
- For each directory found, detect project type:
  - Node: package.json present → read name, scripts.start, main
  - Python: requirements.txt / pyproject.toml → detect framework
  - Docker: docker-compose.yml → read service definitions
  - Static: index.html with no backend markers
- Cross-reference with running processes: pm2 list, systemctl, docker ps
- Cross-reference with nginx/apache configs to find domain mappings
- Create or update projects rows for each discovered project

### **Phase 3 — File Tracking**
- For each discovered project, track its key config files:
  - Nginx site config — parse server\_name, proxy\_pass, ssl\_certificate
  - PM2 ecosystem file — parse app name, script, env
  - Systemd unit file — parse ExecStart, MemoryLimit, Restart
  - .env file — record keys only, never values, mark is\_sensitive=true
  - Docker compose — parse services, ports, volumes
- For each tracked file: read content, hash it, store in tracked\_files
- If file was previously tracked, compute diff — record if changed externally

### **Phase 4 — Memory Extraction**
- After gathering raw data, call Claude to extract structured memories
- Prompt: 'Given this server data, extract key facts as memory entries'
- Claude returns JSON array of {key, value, category, project\_id} objects
- For each: upsert into memories table, generate embedding, cache in Redis
- Example memories extracted by sync:
  - deploy\_command: 'cd /var/www/api && git pull && npm install && pm2 reload api'
  - app\_port: '3000'
  - ssl\_expiry: '2026-08-20'
  - nginx\_config: '/etc/nginx/sites-available/api'

### **Phase 5 — Brain File Generation**
- Generate SERVER.md from server inventory + all projects summary
- Generate {project}.md for each project from its tracked files + memories
- Store each in brain\_versions table with version number
- Write files to ~/.vibe-server/brains/{server}/
- Display sync summary to user

## **4.2 /sync Output**
` `prod ❯ /sync

`  `→ phase 1: server inventory

`  `↳ collecting system info...

`  `✓ Ubuntu 22.04 · 2 vCPU · 4GB · 47% disk

`  `→ phase 2: project discovery

`  `↳ scanning /var/www/, /opt/, /home/...

`  `✓ found 3 projects: api, frontend, worker

`  `→ phase 3: file tracking

`  `↳ reading 8 config files...

`  `⚠ nginx config for api changed since last sync (external edit)

`  `✓ tracked: nginx(2) pm2(1) systemd(1) env(3) cron(1)

`  `→ phase 4: memory extraction

`  `↳ extracting facts from server data...

`  `✓ 14 memories updated, 3 new

`  `→ phase 5: brain files

`  `↳ regenerating SERVER.md (v12)...

`  `↳ regenerating api.md (v8)...

`  `↳ regenerating frontend.md (v3)...

`  `↳ regenerating worker.md (v5)...

`  `✓ brain files written to ~/.vibe-server/brains/prod/

`  `sync complete in 12.4s

`  `→ 3 projects · 8 files tracked · 17 memories · brain v12

## **4.3 /sync Variants**

|**Command**|**Behavior**|
| :- | :- |
|/sync|Full sync — all 5 phases|
|/sync --quick|Phase 1 + 4 only — fast health check, skip file scan|
|/sync --project api|Phases 2-5 for one project only|
|/sync --files|Phase 3 only — re-read tracked files, detect external changes|
|/sync --memory|Phase 4 only — re-extract memories from existing data|


# **5. Memory System**
The memory system is how the AI gets smarter with every session. It has three parts: working memory (Redis — current session), semantic memory (Postgres + pgvector — searchable facts), and brain files (Markdown — structured summaries).

## **5.1 Memory Retrieval at Session Start**
When a session starts, the memory module runs before the first user prompt:

1. Load server brain file (SERVER.md) — inject as system context
1. Load relevant project brain files if a project is in focus
1. Query memories table for this server — top 30 by times\_accessed
1. Cache hot memories in Redis for fast lookup during session
1. Prepend all of this to the AI system prompt

## **5.2 Memory Retrieval During Session**
When the user sends a message, before calling the AI:

1. Extract key entities from user message (project name, file path, command type)
1. Semantic search: embed the user message, query pgvector for similar memories
1. Return top 5 semantically relevant memories
1. Inject them into the current turn context

This means if a user says 'deploy the api' and the memory system has 'deploy\_command: cd /var/www/api && git pull...' — it's automatically in context without the AI having to ask.

## **5.3 Memory Writing**
Memories are written in two ways:

- **AI-inferred:** After every AI response, the AI can include a memories array in its JSON output with new facts to store. The agent should store these automatically.
- **Sync-discovered:** The /sync phases extract and write memories as part of the crawl.
- **User-set:** Via /memory set key value — highest confidence, never overwritten by AI.

## **5.4 Memory Conflict Resolution**
- User-set memories (source='user\_set') are never overwritten automatically
- AI-inferred memories with lower confidence are overwritten by higher confidence discoveries
- If a sync finds a different value than what's in memory, update and log the change
- Confidence degrades over time for memories that haven't been confirmed — decay function applied weekly

## **5.5 /memory Commands**
/memory                    show all memories for current server

/memory --project api      filter by project

/memory --category config  filter by category

/memory set <key> <value>  manually set a memory

/memory forget <key>       delete a memory

/memory search <query>     semantic search across memories

/memory clear              wipe all memories for this server (destructive)


# **6. Pre-Edit Memory Check**
Before making any change to a file or running any write command, vibe-server checks its memory and the current file state. This prevents stale edits and conflicts.

## **6.1 The Check Flow**
1. User requests a change (e.g. 'update nginx to add rate limiting')
1. Memory check: does the AI know where the nginx config is? Does it have a cached read?
1. Freshness check: when was this file last read? If > 10 min ago, re-read from server
1. Hash check: does the current file hash match tracked\_files.content\_hash?
1. If hash mismatch → file changed externally since last read → warn user, show diff, ask to proceed
1. If hash matches → safe to proceed — show planned edit, await confirm
1. Execute edit → write to file\_versions → update tracked\_files hash → queue brain file regen

## **6.2 Conflict UX**
` `prod ❯ add gzip compression to nginx

`  `→ checking nginx config freshness...

`  `⚠ /etc/nginx/nginx.conf changed externally since last read

`     `last read: 14 min ago  |  file mtime: 6 min ago

`  `diff from my last read:

`  `+ gzip\_comp\_level 6;      ← someone already added this

`  `+ gzip\_types text/plain text/css;

`  `looks like gzip was already added manually. do you want me to:

`  `[1] re-read the file and proceed with your request anyway

`  `[2] skip — it looks like what you wanted is already done

`  `[3] show me the full current config first

## **6.3 /undo System**
Every file write stores content\_before in file\_versions. /undo restores the previous version.

` `prod ❯ /undo

`  `last change: /etc/nginx/sites-available/api

`  `changed: 3 minutes ago (session #47)

`  `reason: added rate limiting to /api/ routes

`  `restoring version 7 → version 8 will be rolled back

`  `restore? [y/N]: y

`  `↳ writing previous version...

`  `↳ nginx -t && systemctl reload nginx

`  `✓ reverted. nginx config back to version 7.

` `prod ❯ /undo --file /etc/nginx/sites-available/api --version 5

\# jump back to any specific version


# **7. Brain File Versioning**
Brain files are versioned like git commits. Every regeneration creates a new version in brain\_versions. The diff between versions is human-readable and queryable.

## **7.1 Version Triggers**
- **After /sync:** full regen of all brain files
- **After any file edit:** regen the brain file for that project only
- **After /memory set:** regen if the memory affects a brain file section
- **After incident detected:** append to incident log, regen
- **Manual:** /brain regen [project]

## **7.2 /brain Commands**
/brain                     show current SERVER.md in terminal

/brain api                 show api.md

/brain diff                diff current brain vs previous version

/brain diff api --v 5      diff current api.md vs version 5

/brain history             list all brain versions with timestamps

/brain regen               force regenerate all brain files

/brain export              export all brain files as zip

/brain push                push brain files to a git repo (if configured)

## **7.3 Git Integration (optional)**
Users can configure a git repo to push brain files to. This gives them a full history in GitHub/GitLab and makes brain files shareable with teammates.

\# In ~/.vibe-server/config.yaml

brain\_git:

`  `repo: git@github.com:user/myserver-brain.git

`  `auto\_push: true      # push after every sync

`  `branch: main

- vps brain push — manual push
- Auto-push runs after /sync if configured
- Commit message auto-generated: 'brain v12: 3 projects updated, 2 incidents logged'


# **8. Session Context Building**
On every session start, the context module assembles what the AI knows before the first message. The goal is zero cold-start — the AI should feel like it's continuing a conversation, not starting from scratch.

## **8.1 Context Assembly Order**
1. Base system prompt (vibe-server personality + rules)
1. Mode overlay (general / deploy / debug)
1. Hoster overlay (if hoster detected)
1. SERVER.md brain file content
1. Project brain files for projects accessed in last 3 sessions
1. Top 20 memories by access frequency
1. Last session summary: what was done, what was left incomplete
1. User preferences: verbosity, preferred tools, tone

## **8.2 Last Session Summary**
When a session ends, Claude generates a 3-5 sentence summary of what happened and stores it in the sessions table. The next session starts by reading this:

LAST SESSION (2026-06-14, 47 min):

Investigated OOM crash on the api process. Raised MemoryLimit

to 2GB in /etc/systemd/system/api.service and reloaded systemd.

Root cause (memory leak) not resolved — user was going to check

with Claude Code. SSL cert expires 2026-08-20 — flagged for renewal.

## **8.3 Context Size Management**
- Target: keep total system prompt under 8000 tokens
- Brain files are summarized if full content would exceed budget
- Memories are ranked by relevance to the server + recent access
- If user focuses on a specific project (/project api), load that project's full brain file and drop others
- Use tiktoken to count tokens before assembling — trim from least-relevant end


# **9. Build Order for Coding Agent**
Build in this exact sequence. Each step is independently testable.

1. **Supabase project setup**
   - Create Supabase project
   - Enable pgvector extension: CREATE EXTENSION vector
   - Run migrations for all 7 tables (servers, projects, tracked\_files, file\_versions, memories, brain\_versions, sessions)
   - Set up Supabase auth (email/password for the web app, token for CLI)

1. **Upstash Redis setup**
   - Create Upstash Redis database (serverless, REST API)
   - Implement RedisClient wrapper with all key patterns from Section 2.7
   - Write tests: set/get session state, pending changes list, memory cache

1. **Database layer (db/)**
   - ORM models matching all 7 tables exactly as specced
   - Repository classes: ServerRepo, ProjectRepo, FileRepo, MemoryRepo, BrainRepo
   - Each repo has: create, get, update, delete, list — typed, no raw SQL
   - Write tests for all repos with a test Supabase project

1. **Memory module (memory/)**
   - MemoryWriter: upsert memory, generate embedding via Anthropic, store vector
   - MemoryRetriever: semantic search via pgvector, keyword search fallback
   - MemoryCache: Redis hot-cache load/refresh
   - Conflict resolution logic: user\_set always wins

1. **/sync implementation (sync/)**
   - Phase 1 — server inventory: all commands, snapshot writer
   - Phase 2 — project discovery: scanner with type detection
   - Phase 3 — file tracking: reader, hasher, diff detector
   - Phase 4 — memory extraction: Claude call with extraction prompt
   - Phase 5 — brain file generation: template + Claude call to write markdown
   - Sync orchestrator: runs all phases, handles errors per phase, displays progress

1. **Pre-edit check + file write system**
   - FileEditor: read → hash check → diff → confirm → write → version → regen brain
   - file\_versions writer
   - /undo implementation: lookup last version, restore, reload service

1. **Context builder (context/)**
   - ContextAssembler: loads brain files, memories, last session summary, assembles system prompt
   - Token counter: stays under 8000 token budget
   - Project focus mode: /project api loads full project context

1. **Session lifecycle updates**
   - On connect: snapshot → load brain → load memories → create session → assemble context
   - On disconnect: generate session summary via Claude → store → update session row

1. **Slash command implementations**
   - /sync (all variants), /memory (all variants), /brain (all variants), /undo, /diff

1. **Backend API (for subscription model)**
   - POST /session/start — auth check, create session, return context
   - POST /ai/complete — proxy to Claude with memory injection
   - POST /sync — run sync for authenticated server
   - GET /brain/{server} — return brain files
   - Stripe subscription check middleware

1. **Tests + integration**
   - Unit: all repos, memory module, sync phases (mocked SSH)
   - Integration: full /sync against Docker Ubuntu test server
   - E2E: connect → sync → edit file → undo → verify version history


# **10. Services & Infrastructure Summary**

|**Service**|**Provider**|**Cost**|**What it does**|
| :- | :- | :- | :- |
|PostgreSQL|Supabase|Free tier|All persistent data + pgvector embeddings|
|Redis|Upstash|Free tier|Session state, hot memory cache|
|AI|Anthropic|Your backend pays|Claude for completions + embeddings|
|Auth|Supabase Auth|Included|User accounts, JWT tokens for CLI|
|Backend API|Railway/Render|~$5/mo|Your FastAPI/Express proxy server|
|Brain git sync|GitHub/GitLab|Free|Optional — user's own repo|
|Payments|Stripe|2\.9% + 30¢|Subscription management|

Total infrastructure cost at launch: under $10/month. Supabase and Upstash free tiers are generous enough to get to hundreds of users before you need to upgrade.



vibe-server Memory System Spec v1.0 — hand to coding agent
