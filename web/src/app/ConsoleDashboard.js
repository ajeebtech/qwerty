"use client";

import React, { useState } from "react";
import { 
  Server, Shield, Cpu, RefreshCw, Layers, Settings, Plus, Trash2, Search, Terminal, Play, CheckCircle, AlertCircle
} from "lucide-react";

export default function ConsoleDashboard({
  servers,
  setServers,
  settings,
  setSettings,
  memories,
  setMemories,
  sessions,
  setSessions,
  commands,
  setCommands,
  snapshots,
  setSnapshots
}) {
  const [activeServer, setActiveServer] = useState(servers[0]?.name || "dev-vps");
  const [activeTab, setActiveTab] = useState("logs");
  const [searchTerm, setSearchTerm] = useState("");

  // Server creation state
  const [newServerName, setNewServerName] = useState("");
  const [newServerHost, setNewServerHost] = useState("");
  const [newServerUser, setNewServerUser] = useState("");
  const [newServerPort, setNewServerPort] = useState("22");
  const [newServerProvider, setNewServerProvider] = useState("aws");

  // Memory creation state
  const [newMemKey, setNewMemKey] = useState("");
  const [newMemVal, setNewMemVal] = useState("");

  // Selected session state (for logs tab)
  const serverSessions = sessions.filter(s => s.server_name === activeServer);
  const [selectedSessionId, setSelectedSessionId] = useState(
    serverSessions[serverSessions.length - 1]?.id || ""
  );

  // Command input execution simulation
  const [cmdInput, setCmdInput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);

  // Snapshot states
  const serverSnapshots = snapshots.filter(s => s.server_name === activeServer);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState(
    serverSnapshots[serverSnapshots.length - 1]?.id || ""
  );
  const [diffBaseSnapshotId, setDiffBaseSnapshotId] = useState("");

  // Retrieve current active server configurations & settings
  const currentServerObj = servers.find(s => s.name === activeServer);
  const globalLogColor = settings.find(s => s.server_name === null && s.key === "log_color")?.value || "#818cf8";
  const serverLogColor = settings.find(s => s.server_name === activeServer && s.key === "log_color")?.value || globalLogColor;
  const anthropicKey = settings.find(s => s.server_name === null && s.key === "anthropic_api_key")?.value || "";
  const preferredWebServer = settings.find(s => s.server_name === null && s.key === "preferred_web_server")?.value || "nginx";
  const preferredEditor = settings.find(s => s.server_name === null && s.key === "preferred_editor")?.value || "vim";

  // Temporary Settings Edit Form State
  const [tempLogColor, setTempLogColor] = useState(serverLogColor);
  const [tempApiKey, setTempApiKey] = useState(anthropicKey);
  const [tempWebServer, setTempWebServer] = useState(preferredWebServer);
  const [tempEditor, setTempEditor] = useState(preferredEditor);

  // Sync temp setting edits when active server changes
  React.useEffect(() => {
    setTempLogColor(serverLogColor);
  }, [activeServer, serverLogColor]);

  const handleAddServer = (e) => {
    e.preventDefault();
    if (!newServerName || !newServerHost || !newServerUser) return;
    const newServer = {
      name: newServerName.trim().toLowerCase(),
      host: newServerHost.trim(),
      user: newServerUser.trim(),
      port: parseInt(newServerPort) || 22,
      status: "online",
      provider: newServerProvider
    };
    setServers([...servers, newServer]);
    setActiveServer(newServer.name);
    setNewServerName("");
    setNewServerHost("");
    setNewServerUser("");
    setNewServerPort("22");
  };

  const handleAddMemory = (e) => {
    e.preventDefault();
    if (!newMemKey || !newMemVal) return;
    const newRecord = {
      id: Date.now(),
      server_name: activeServer,
      key: newMemKey.trim().toLowerCase(),
      value: newMemVal.trim(),
      source: "user_set",
      updated_at: new Date().toISOString()
    };
    setMemories([...memories, newRecord]);
    setNewMemKey("");
    setNewMemVal("");
  };

  const handleDeleteMemory = (id) => {
    setMemories(memories.filter(m => m.id !== id));
  };

  const handleMockExecute = (e) => {
    e.preventDefault();
    if (!cmdInput.trim() || isExecuting) return;

    setIsExecuting(true);
    const cmd = cmdInput.trim();

    // Create session if none selected
    let sessId = selectedSessionId;
    if (!sessId) {
      sessId = Date.now();
      const newSessObj = {
        id: sessId,
        server_name: activeServer,
        host: currentServerObj?.host || "127.0.0.1",
        user: currentServerObj?.user || "root",
        started_at: new Date().toISOString(),
        ended_at: null,
        mode: "standard",
        command_count: 1,
        notes: "On-demand interactive session log."
      };
      setSessions(prev => [...prev, newSessObj]);
      setSelectedSessionId(sessId);
    } else {
      setSessions(prev => prev.map(s => s.id === sessId ? { ...s, command_count: s.command_count + 1 } : s));
    }

    setTimeout(() => {
      const isDocker = cmd.includes("docker");
      const isSystem = cmd.includes("systemctl") || cmd.includes("service");
      let mockOutput = `Executing standard shell operation: '${cmd}'\nCompleted successfully.`;
      if (isDocker) {
        mockOutput = `CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS         PORTS\n9f8b7c6a5d4e   redis:alpine  "docker-entrypoint.s…"  2 hours ago     Up 2 hours     0.0.0.0:6379->6379/tcp   redis-cache`;
      } else if (isSystem) {
        mockOutput = `● service.service - Simulated Daemon\n   Loaded: loaded (/lib/systemd/system/daemon.service; enabled)\n   Active: active (running) since Sun 2026-06-14 12:00:00 UTC\n Main PID: 40592\n   Memory: 15.2M`;
      } else if (cmd === "ls -la") {
        mockOutput = `total 24\ndrwxr-xr-x  3 root root 4096 Jun 14 18:00 .\ndrwxr-xr-x 22 root root 4096 Jun 14 15:40 ..\n-rw-r--r--  1 root root  512 Jun 14 18:12 config.yaml\n-rw-r--r--  1 root root 8192 Jun 14 18:25 data.db`;
      }

      const newCmd = {
        id: Date.now(),
        session_id: sessId,
        server_name: activeServer,
        command: cmd,
        description: `Executed via interactive control dashboard`,
        output: mockOutput,
        exit_code: 0,
        duration_ms: Math.floor(Math.random() * 200) + 50,
        ran_at: new Date().toISOString(),
        was_dry_run: false,
        user_prompt: "Interactive dashboard input"
      };

      setCommands(prev => [...prev, newCmd]);
      setIsExecuting(false);
      setCmdInput("");
    }, 1000);
  };

  const handleSaveSettings = (e) => {
    e.preventDefault();
    // Update local settings state
    let updatedSettings = [...settings];

    // Handle global API Key
    const apiKeyIdx = updatedSettings.findIndex(s => s.server_name === null && s.key === "anthropic_api_key");
    if (apiKeyIdx >= 0) {
      updatedSettings[apiKeyIdx].value = tempApiKey;
    } else {
      updatedSettings.push({ server_name: null, key: "anthropic_api_key", value: tempApiKey });
    }

    // Handle global Web Server
    const webServerIdx = updatedSettings.findIndex(s => s.server_name === null && s.key === "preferred_web_server");
    if (webServerIdx >= 0) {
      updatedSettings[webServerIdx].value = tempWebServer;
    } else {
      updatedSettings.push({ server_name: null, key: "preferred_web_server", value: tempWebServer });
    }

    // Handle global preferred editor
    const editorIdx = updatedSettings.findIndex(s => s.server_name === null && s.key === "preferred_editor");
    if (editorIdx >= 0) {
      updatedSettings[editorIdx].value = tempEditor;
    } else {
      updatedSettings.push({ server_name: null, key: "preferred_editor", value: tempEditor });
    }

    // Handle server-specific log color
    const colorIdx = updatedSettings.findIndex(s => s.server_name === activeServer && s.key === "log_color");
    if (colorIdx >= 0) {
      updatedSettings[colorIdx].value = tempLogColor;
    } else {
      updatedSettings.push({ server_name: activeServer, key: "log_color", value: tempLogColor });
    }

    setSettings(updatedSettings);
    alert("Configurations saved locally!");
  };

  // Log filter results
  const filteredCommands = commands
    .filter(c => c.server_name === activeServer && (!selectedSessionId || c.session_id === parseInt(selectedSessionId)))
    .filter(c => {
      const searchLower = searchTerm.toLowerCase();
      return (
        c.command.toLowerCase().includes(searchLower) ||
        (c.output && c.output.toLowerCase().includes(searchLower)) ||
        (c.user_prompt && c.user_prompt.toLowerCase().includes(searchLower))
      );
    });

  // Memories filter
  const filteredMemories = memories
    .filter(m => m.server_name === activeServer)
    .filter(m => {
      const searchLower = searchTerm.toLowerCase();
      return m.key.includes(searchLower) || m.value.toLowerCase().includes(searchLower);
    });

  // Current selected snapshot metrics
  const activeSnapshot = serverSnapshots.find(s => s.id === parseInt(selectedSnapshotId));
  const baseSnapshot = serverSnapshots.find(s => s.id === parseInt(diffBaseSnapshotId));

  // Memory/Disk percentage compute
  const memPct = activeSnapshot ? Math.round((activeSnapshot.memory_used_mb / activeSnapshot.memory_total_mb) * 100) : 0;
  const diskPct = activeSnapshot ? Math.round((activeSnapshot.disk_used_gb / activeSnapshot.disk_total_gb) * 100) : 0;
  const loadAvgs = activeSnapshot ? JSON.parse(activeSnapshot.load_avg) : [0, 0, 0];

  return (
    <div className="dashboard-layout">
      {/* Sidebar: Servers Connections */}
      <aside className="sidebar">
        <div className="sidebar-title">
          <span>Registered VPS</span>
          <Server size={14} />
        </div>

        <div className="server-list">
          {servers.map(s => (
            <div 
              key={s.name} 
              className={`server-item ${activeServer === s.name ? "active" : ""}`}
              onClick={() => {
                setActiveServer(s.name);
                const serverSess = sessions.filter(x => x.server_name === s.name);
                setSelectedSessionId(serverSess[serverSess.length - 1]?.id || "");
                const serverSnaps = snapshots.filter(x => x.server_name === s.name);
                setSelectedSnapshotId(serverSnaps[serverSnaps.length - 1]?.id || "");
                setDiffBaseSnapshotId("");
              }}
            >
              <div className="server-info">
                <span className={`server-status-dot ${s.status}`}></span>
                <div>
                  <div className="server-name">{s.name}</div>
                  <div className="server-host">{s.host}:{s.port}</div>
                </div>
              </div>
              <span className="server-provider-badge">{s.provider}</span>
            </div>
          ))}
        </div>

        {/* Add Connection Widget */}
        <div style={{ marginTop: "auto", borderTop: "1px solid var(--border-color)", paddingTop: "20px" }}>
          <h4 className="sidebar-form-title">Register New Host</h4>
          <form onSubmit={handleAddServer}>
            <div className="form-group">
              <label className="form-label">Server Alias</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. production-api" 
                value={newServerName}
                onChange={e => setNewServerName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Host IP Address</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="192.168.1.1" 
                value={newServerHost}
                onChange={e => setNewServerHost(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">User / Port</label>
              <div style={{ display: "flex", gap: "8px" }}>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="root" 
                  value={newServerUser}
                  onChange={e => setNewServerUser(e.target.value)}
                  style={{ flex: 2 }}
                  required
                />
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="22" 
                  value={newServerPort}
                  onChange={e => setNewServerPort(e.target.value)}
                  style={{ flex: 1 }}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Cloud Hoster</label>
              <select 
                className="form-input" 
                value={newServerProvider}
                onChange={e => setNewServerProvider(e.target.value)}
              >
                <option value="aws">AWS EC2</option>
                <option value="gcp">Google Cloud</option>
                <option value="digitalocean">DigitalOcean</option>
                <option value="local-sim">Local Simulator</option>
              </select>
            </div>
            <button type="submit" className="form-btn">
              <Plus size={14} style={{ marginRight: "4px", verticalAlign: "middle" }} /> Add Profile
            </button>
          </form>
        </div>
      </aside>

      {/* Main Dashboard Panel */}
      <main className="dashboard-main">
        {/* Navigation / Tabs */}
        <nav className="dashboard-nav">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Terminal size={18} style={{ color: "var(--accent-secondary)" }} />
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", fontWeight: "600" }}>
              console.website.com <span style={{ color: "var(--text-muted)", fontWeight: "400" }}>/</span> {activeServer}
            </h2>
          </div>

          <div className="dashboard-tabs">
            <button 
              className={`dashboard-tab ${activeTab === "logs" ? "active" : ""}`}
              onClick={() => { setActiveTab("logs"); setSearchTerm(""); }}
            >
              <Terminal size={16} /> Connection Logs
            </button>
            <button 
              className={`dashboard-tab ${activeTab === "memory" ? "active" : ""}`}
              onClick={() => { setActiveTab("memory"); setSearchTerm(""); }}
            >
              <Layers size={16} /> AI memory
            </button>
            <button 
              className={`dashboard-tab ${activeTab === "snapshots" ? "active" : ""}`}
              onClick={() => { setActiveTab("snapshots"); setSearchTerm(""); }}
            >
              <Cpu size={16} /> Snapshots Diff
            </button>
            <button 
              className={`dashboard-tab ${activeTab === "settings" ? "active" : ""}`}
              onClick={() => { setActiveTab("settings"); setSearchTerm(""); }}
            >
              <Settings size={16} /> Settings
            </button>
          </div>
        </nav>

        {/* Tab Contents */}
        <div className="tab-content">
          {/* logs tab */}
          {activeTab === "logs" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px", height: "100%" }}>
              {/* Filter controls */}
              <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span className="form-label">Active SSH Session</span>
                  <select 
                    className="form-input" 
                    value={selectedSessionId} 
                    onChange={e => setSelectedSessionId(e.target.value)}
                    style={{ width: "260px" }}
                  >
                    <option value="">-- All Session Histories --</option>
                    {serverSessions.map(s => (
                      <option key={s.id} value={s.id}>
                        Session #{s.id} ({new Date(s.started_at).toLocaleTimeString()}) - {s.command_count} cmds
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1 }}>
                  <span className="form-label">Search commands / output</span>
                  <div style={{ position: "relative" }}>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="Filter by keyword..." 
                      value={searchTerm} 
                      onChange={e => setSearchTerm(e.target.value)}
                      style={{ paddingLeft: "32px" }}
                    />
                    <Search size={14} style={{ position: "absolute", left: "10px", top: "11px", color: "var(--text-muted)" }} />
                  </div>
                </div>
              </div>

              {/* Logs Stream Panel */}
              <div className="console-wrapper">
                <div className="console-header-bar">
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                    <span style={{ display: "inline-block", width: "8px", height: "8px", background: serverLogColor, borderRadius: "50%" }}></span>
                    <span>Active SSH color: <code style={{ color: serverLogColor }}>{serverLogColor}</code></span>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                    {filteredCommands.length} matches found
                  </div>
                </div>

                <div className="console-logs-feed">
                  {filteredCommands.length === 0 ? (
                    <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px" }}>
                      <AlertCircle size={24} style={{ margin: "0 auto 12px", display: "block" }} />
                      No matching connection logs found.
                    </div>
                  ) : (
                    filteredCommands.map(c => (
                      <div key={c.id} className="log-entry">
                        <div className="log-meta">
                          <span className="log-session-badge">Sess #{c.session_id}</span>
                          <span>{new Date(c.ran_at).toLocaleTimeString()}</span>
                          <span className="log-duration">{c.duration_ms}ms</span>
                          {c.was_dry_run && <span style={{ color: "var(--accent-warning)" }}>[DRY RUN]</span>}
                          {c.exit_code === 0 ? (
                            <span style={{ color: "var(--accent-success)", display: "flex", alignItems: "center", gap: "2px" }}>
                              <CheckCircle size={10} style={{ color: "var(--accent-success)" }} /> exit 0
                            </span>
                          ) : (
                            <span style={{ color: "var(--accent-danger)" }}>exit {c.exit_code}</span>
                          )}
                        </div>
                        {c.user_prompt && (
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                            Prompt: "{c.user_prompt}"
                          </div>
                        )}
                        <div className="log-command-line">
                          <span style={{ color: "var(--text-secondary)" }}>$</span>{" "}
                          <span style={{ color: serverLogColor }}>{c.command}</span>
                        </div>
                        {c.output && (
                          <pre className="log-output-container">{c.output}</pre>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {/* Console prompt execution */}
                <form onSubmit={handleMockExecute} style={{ display: "flex", borderTop: "1px solid var(--border-color)", padding: "12px" }}>
                  <span style={{ padding: "8px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>$</span>
                  <input
                    type="text"
                    className="cli-input-field"
                    placeholder={isExecuting ? "Executing command plan safely..." : "Execute interactive shell command on host (e.g. docker ps, ls -la)..."}
                    value={cmdInput}
                    onChange={e => setCmdInput(e.target.value)}
                    disabled={isExecuting}
                    style={{ background: "transparent", color: "var(--text-primary)", border: "none", flex: 1, outline: "none", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}
                  />
                  <button 
                    type="submit" 
                    className="btn-primary" 
                    style={{ padding: "6px 14px", fontSize: "0.8rem", borderRadius: "4px" }}
                    disabled={isExecuting || !cmdInput.trim()}
                  >
                    {isExecuting ? <RefreshCw className="animate-spin" size={12} /> : <Play size={12} />}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* AI Memory Manager */}
          {activeTab === "memory" && (
            <div className="memory-grid">
              <div style={{ display: "flex", justifySpace: "between", alignItems: "center" }}>
                <div>
                  <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "4px" }}>AI System Memory Context</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Persistent details inferred dynamically or manually explicitly linked to {activeServer}.</p>
                </div>
                <div style={{ marginLeft: "auto", position: "relative" }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search memory..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    style={{ paddingLeft: "32px", width: "200px" }}
                  />
                  <Search size={14} style={{ position: "absolute", left: "10px", top: "11px", color: "var(--text-muted)" }} />
                </div>
              </div>

              {/* Memory Data Table */}
              <div className="memory-table-card">
                <table className="memory-table">
                  <thead>
                    <tr>
                      <th>Key Reference</th>
                      <th>Saved Context Value</th>
                      <th>Source Type</th>
                      <th>Last Updated</th>
                      <th style={{ width: "80px", textAlign: "center" }}>Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMemories.length === 0 ? (
                      <tr>
                        <td colSpan="5" style={{ textAlign: "center", color: "var(--text-muted)", padding: "30px" }}>
                          No registered memory facts found.
                        </td>
                      </tr>
                    ) : (
                      filteredMemories.map(m => (
                        <tr key={m.id}>
                          <td><code className="memory-key">{m.key}</code></td>
                          <td style={{ color: "var(--text-primary)" }}>{m.value}</td>
                          <td>
                            <span className={`memory-source-badge ${m.source}`}>
                              {m.source === "ai_inferred" ? "AI Inferred" : "User Added"}
                            </span>
                          </td>
                          <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                            {new Date(m.updated_at).toLocaleDateString()}
                          </td>
                          <td style={{ textAlign: "center" }}>
                            <button className="memory-delete-btn" onClick={() => handleDeleteMemory(m.id)}>
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Add Memory Fact Form */}
              <div className="settings-section-card" style={{ maxWidth: "500px" }}>
                <h4 style={{ fontSize: "0.95rem", fontWeight: "600", marginBottom: "12px" }}>Teach Agent New Local Context</h4>
                <form onSubmit={handleAddMemory} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <div style={{ flex: 1 }}>
                      <label className="form-label">Memory Key</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="e.g. api_port" 
                        value={newMemKey} 
                        onChange={e => setNewMemKey(e.target.value)} 
                        required
                      />
                    </div>
                    <div style={{ flex: 2 }}>
                      <label className="form-label">Context Value</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="e.g. 8080" 
                        value={newMemVal} 
                        onChange={e => setNewMemVal(e.target.value)} 
                        required
                      />
                    </div>
                  </div>
                  <button type="submit" className="form-btn" style={{ alignSelf: "flex-end", padding: "8px 16px" }}>
                    Insert Key
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Snapshot Diff Panel */}
          {activeTab === "snapshots" && (
            <div className="snapshot-overview">
              {/* Snapshot Select list */}
              <div className="snapshot-card">
                <h3 style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "16px" }}>System Snapshots</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {serverSnapshots.map(snap => (
                    <div 
                      key={snap.id} 
                      className={`server-item ${selectedSnapshotId === snap.id.toString() ? "active" : ""}`}
                      onClick={() => {
                        setSelectedSnapshotId(snap.id.toString());
                        setDiffBaseSnapshotId("");
                      }}
                      style={{ padding: "14px" }}
                    >
                      <div>
                        <div style={{ fontSize: "0.85rem", fontWeight: "600" }}>Snapshot #{snap.id}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                          {new Date(snap.captured_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  {serverSnapshots.length === 0 && (
                    <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "20px" }}>
                      No health snapshots found.
                    </div>
                  )}
                </div>
              </div>

              {/* Snapshot Detail & Diff comparison */}
              {activeSnapshot ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div className="snapshot-card">
                    <div className="snapshot-header">
                      <div>
                        <h3 style={{ fontSize: "1.2rem", fontWeight: "700" }}>Snapshot #{activeSnapshot.id} Details</h3>
                        <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                          Captured at {new Date(activeSnapshot.captured_at).toLocaleString()}
                        </span>
                      </div>
                      <span style={{ fontSize: "0.75rem", padding: "4px 8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px", color: "var(--text-secondary)" }}>
                        {activeSnapshot.os_info}
                      </span>
                    </div>

                    <div className="metric-bars">
                      <div className="metric-bar-group">
                        <div className="metric-label-row">
                          <span>RAM Allocation</span>
                          <span>{activeSnapshot.memory_used_mb}MB / {activeSnapshot.memory_total_mb}MB ({memPct}%)</span>
                        </div>
                        <div className="metric-track">
                          <div className="metric-fill cyan" style={{ width: `${memPct}%` }}></div>
                        </div>
                      </div>

                      <div className="metric-bar-group">
                        <div className="metric-label-row">
                          <span>Disk Capacity (/)</span>
                          <span>{activeSnapshot.disk_used_gb}GB / {activeSnapshot.disk_total_gb}GB ({diskPct}%)</span>
                        </div>
                        <div className="metric-track">
                          <div className="metric-fill purple" style={{ width: `${diskPct}%` }}></div>
                        </div>
                      </div>

                      <div className="metric-bar-group">
                        <div className="metric-label-row">
                          <span>CPU Average Load</span>
                          <span>{loadAvgs.join(", ")} ({activeSnapshot.cpu_count} Cores)</span>
                        </div>
                        <div className="metric-track">
                          <div className="metric-fill amber" style={{ width: `${Math.min(loadAvgs[0] * 100, 100)}%` }}></div>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "20px" }}>
                      <div>
                        <h4 style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "8px", fontWeight: "600" }}>Running Services</h4>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {JSON.parse(activeSnapshot.running_services).map(srv => (
                            <span key={srv} style={{ fontSize: "0.75rem", padding: "3px 8px", background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "4px", color: "var(--accent-success)" }}>
                              {srv}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "8px", fontWeight: "600" }}>Listening Ports</h4>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {JSON.parse(activeSnapshot.open_ports).map(port => (
                            <span key={port} style={{ fontSize: "0.75rem", padding: "3px 8px", background: "rgba(99, 102, 241, 0.08)", border: "1px solid rgba(99, 102, 241, 0.2)", borderRadius: "4px", color: "var(--accent-secondary)" }}>
                              :{port}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Diff tool widget */}
                  <div className="snapshot-card">
                    <h3 style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "12px" }}>Compare with Baseline Snapshot</h3>
                    <div style={{ display: "flex", gap: "12px", marginBottom: "16px", alignItems: "center" }}>
                      <select 
                        className="form-input" 
                        value={diffBaseSnapshotId}
                        onChange={e => setDiffBaseSnapshotId(e.target.value)}
                        style={{ width: "240px" }}
                      >
                        <option value="">-- Select Baseline Snapshot --</option>
                        {serverSnapshots.filter(s => s.id !== activeSnapshot.id).map(s => (
                          <option key={s.id} value={s.id}>
                            Snapshot #{s.id} ({new Date(s.captured_at).toLocaleDateString()})
                          </option>
                        ))}
                      </select>
                    </div>

                    {baseSnapshot && (
                      <div className="diff-container">
                        <div className="diff-line diff-header">
                          <span>--- Snapshot #{baseSnapshot.id}</span>
                          <span>+++ Snapshot #{activeSnapshot.id}</span>
                        </div>
                        {/* Compute diff variables */}
                        {(() => {
                          const baseServices = JSON.parse(baseSnapshot.running_services);
                          const activeServices = JSON.parse(activeSnapshot.running_services);
                          const basePorts = JSON.parse(baseSnapshot.open_ports);
                          const activePorts = JSON.parse(activeSnapshot.open_ports);

                          const addedServices = activeServices.filter(s => !baseServices.includes(s));
                          const removedServices = baseServices.filter(s => !activeServices.includes(s));
                          const addedPorts = activePorts.filter(p => !basePorts.includes(p));
                          const removedPorts = basePorts.filter(p => !activePorts.includes(p));

                          const hasChanges = 
                            addedServices.length > 0 || removedServices.length > 0 ||
                            addedPorts.length > 0 || removedPorts.length > 0 ||
                            baseSnapshot.memory_used_mb !== activeSnapshot.memory_used_mb;

                          return (
                            <>
                              <div className="diff-line">
                                <span>@@ -1,4 +1,4 @@ System Resources:</span>
                              </div>
                              <div className="diff-line">
                                <span className={activeSnapshot.memory_used_mb > baseSnapshot.memory_used_mb ? "diff-added" : "diff-removed"}>
                                  {activeSnapshot.memory_used_mb > baseSnapshot.memory_used_mb ? "+" : "-"} Memory usage: {activeSnapshot.memory_used_mb}MB (Diff: {activeSnapshot.memory_used_mb - baseSnapshot.memory_used_mb}MB)
                                </span>
                              </div>
                              {removedServices.map(s => (
                                <div key={s} className="diff-line diff-removed">
                                  <span>- Service: {s} [STOPPED]</span>
                                </div>
                              ))}
                              {addedServices.map(s => (
                                <div key={s} className="diff-line diff-added">
                                  <span>+ Service: {s} [RUNNING]</span>
                                </div>
                              ))}
                              {removedPorts.map(p => (
                                <div key={p} className="diff-line diff-removed">
                                  <span>- Port listening: :{p} [CLOSED]</span>
                                </div>
                              ))}
                              {addedPorts.map(p => (
                                <div key={p} className="diff-line diff-added">
                                  <span>+ Port listening: :{p} [OPENED]</span>
                                </div>
                              ))}
                              {!hasChanges && (
                                <div className="diff-line" style={{ color: "var(--text-muted)" }}>
                                  No system configuration differences found.
                                </div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", padding: "40px" }}>
                  Select a snapshot to inspect.
                </div>
              )}
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === "settings" && (
            <div className="settings-grid">
              <div className="settings-section-card">
                <h3 className="settings-title">Global CLI Settings</h3>
                <form onSubmit={handleSaveSettings}>
                  <div className="settings-input-group">
                    <label className="settings-label">Anthropic API Key</label>
                    <input 
                      type="password" 
                      className="settings-input" 
                      placeholder="sk-ant-..." 
                      value={tempApiKey}
                      onChange={e => setTempApiKey(e.target.value)}
                    />
                    <div className="settings-desc">Stored in local config.yaml, never committed to git repos.</div>
                  </div>

                  <div className="settings-input-group">
                    <label className="settings-label">Preferred Web Server</label>
                    <select 
                      className="settings-input" 
                      value={tempWebServer}
                      onChange={e => setTempWebServer(e.target.value)}
                    >
                      <option value="nginx">Nginx</option>
                      <option value="apache">Apache HTTP Server</option>
                      <option value="caddy">Caddy Web Server</option>
                    </select>
                    <div className="settings-desc">Default tool template suggestions generated during plan design.</div>
                  </div>

                  <div className="settings-input-group">
                    <label className="settings-label">Preferred Command Editor</label>
                    <select 
                      className="settings-input" 
                      value={tempEditor}
                      onChange={e => setTempEditor(e.target.value)}
                    >
                      <option value="vim">Vim</option>
                      <option value="nano">Nano</option>
                      <option value="emacs">Emacs</option>
                    </select>
                  </div>

                  <h3 className="settings-title" style={{ marginTop: "32px" }}>Server-Specific Visual Theme</h3>

                  <div className="settings-input-group">
                    <label className="settings-label">Log Command Accent Color ({activeServer})</label>
                    <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                      <input 
                        type="color" 
                        className="settings-input" 
                        style={{ width: "60px", height: "40px", padding: "2px", cursor: "pointer" }}
                        value={tempLogColor}
                        onChange={e => setTempLogColor(e.target.value)}
                      />
                      <input 
                        type="text" 
                        className="settings-input" 
                        value={tempLogColor}
                        onChange={e => setTempLogColor(e.target.value)}
                        style={{ fontFamily: "var(--font-mono)", width: "120px" }}
                      />
                      {/* Presets */}
                      <div style={{ display: "flex", gap: "6px" }}>
                        {["#00ffcc", "#ff007f", "#a855f7", "#3b82f6", "#f59e0b"].map(c => (
                          <span 
                            key={c} 
                            onClick={() => setTempLogColor(c)}
                            style={{ 
                              display: "inline-block", 
                              width: "20px", 
                              height: "20px", 
                              background: c, 
                              borderRadius: "50%", 
                              cursor: "pointer",
                              border: tempLogColor === c ? "2px solid #fff" : "1px solid rgba(255,255,255,0.2)"
                            }}
                          ></span>
                        ))}
                      </div>
                    </div>
                    <div className="settings-desc">Tailors the syntax highlights inside the Console connection logs.</div>
                  </div>

                  <button type="submit" className="settings-save-btn">
                    Save Client Settings
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
