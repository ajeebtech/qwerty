"use client";

import React, { useState, useEffect } from "react";
import LandingPage from "./LandingPage";
import ConsoleDashboard from "./ConsoleDashboard";
import { RefreshCw } from "lucide-react";
import {
  INITIAL_SERVERS,
  INITIAL_SETTINGS,
  INITIAL_AI_MEMORY,
  INITIAL_SESSIONS,
  INITIAL_COMMANDS,
  INITIAL_SNAPSHOTS
} from "./mockData";

export default function Home() {
  const [currentDomain, setCurrentDomain] = useState("website.com");
  const [isMounted, setIsMounted] = useState(false);

  // States initialized lazily in useEffect to avoid Next.js hydration mismatch
  const [servers, setServers] = useState([]);
  const [settings, setSettings] = useState([]);
  const [memories, setMemories] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [commands, setCommands] = useState([]);
  const [snapshots, setSnapshots] = useState([]);

  useEffect(() => {
    // Hydrate state from localStorage
    const getStored = (key, defaultValue) => {
      const data = localStorage.getItem(`qwerty_${key}`);
      return data ? JSON.parse(data) : defaultValue;
    };

    setServers(getStored("servers", INITIAL_SERVERS));
    setSettings(getStored("settings", INITIAL_SETTINGS));
    setMemories(getStored("memory", INITIAL_AI_MEMORY));
    setSessions(getStored("sessions", INITIAL_SESSIONS));
    setCommands(getStored("commands", INITIAL_COMMANDS));
    setSnapshots(getStored("snapshots", INITIAL_SNAPSHOTS));

    // Subdomain routing detection
    if (typeof window !== "undefined") {
      const host = window.location.hostname;
      if (host.startsWith("console.")) {
        setCurrentDomain("console.website.com");
      } else {
        setCurrentDomain("website.com");
      }
    }

    setIsMounted(true);
  }, []);

  // Sync to LocalStorage on updates
  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_servers", JSON.stringify(servers)); 
  }, [servers, isMounted]);
  
  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_settings", JSON.stringify(settings)); 
  }, [settings, isMounted]);

  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_memory", JSON.stringify(memories)); 
  }, [memories, isMounted]);

  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_sessions", JSON.stringify(sessions)); 
  }, [sessions, isMounted]);

  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_commands", JSON.stringify(commands)); 
  }, [commands, isMounted]);

  useEffect(() => { 
    if (isMounted) localStorage.setItem("qwerty_snapshots", JSON.stringify(snapshots)); 
  }, [snapshots, isMounted]);

  if (!isMounted) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", backgroundColor: "#08090c", color: "#f8fafc", fontFamily: "var(--font-display)" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
          <RefreshCw className="animate-spin" size={32} style={{ color: "var(--accent-secondary)" }} />
          <span>Hydrating Local Config...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="main-wrapper" style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* Main View Manager */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {currentDomain === "website.com" ? (
          <LandingPage onEnterConsole={() => setCurrentDomain("console.website.com")} />
        ) : (
          <ConsoleDashboard
            servers={servers}
            setServers={setServers}
            settings={settings}
            setSettings={setSettings}
            memories={memories}
            setMemories={setMemories}
            sessions={sessions}
            setSessions={setSessions}
            commands={commands}
            setCommands={setCommands}
            snapshots={snapshots}
            setSnapshots={setSnapshots}
          />
        )}
      </div>
    </div>
  );
}
