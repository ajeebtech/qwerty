import { NextResponse } from "next/server";
import { supabase } from "../../lib/supabase";

export async function GET() {
  if (!supabase) {
    return NextResponse.json({
      configured: false,
      servers: [],
      settings: [],
      memories: [],
      sessions: [],
      commands: [],
      snapshots: [],
      projects: []
    });
  }

  try {
    const [
      { data: sessions },
      { data: commands },
      { data: memories },
      { data: settings },
      { data: snapshots },
      { data: projects }
    ] = await Promise.all([
      supabase.from("sessions").select("*").order("id", { ascending: true }),
      supabase.from("commands").select("*").order("id", { ascending: true }),
      supabase.from("ai_memory").select("*").order("id", { ascending: true }),
      supabase.from("settings").select("*").order("id", { ascending: true }),
      supabase.from("server_snapshots").select("*").order("id", { ascending: true }),
      supabase.from("projects").select("*").order("id", { ascending: true })
    ]);

    // Derive unique servers from records
    const serverNames = Array.from(new Set([
      ...(sessions?.map(s => s.server_name) || []),
      ...(commands?.map(c => c.server_name) || []),
      ...(memories?.map(m => m.server_name) || []),
      ...(snapshots?.map(s => s.server_name) || []),
      ...(projects?.map(p => p.server_name) || [])
    ]));

    // Construct server profiles
    const servers = serverNames.map(name => {
      const sess = sessions?.find(s => s.server_name === name);
      const proj = projects?.find(p => p.server_name === name);
      return {
        name,
        host: sess?.host || "127.0.0.1",
        user: sess?.user || "root",
        port: 22,
        status: "online",
        provider: proj?.type || "unknown"
      };
    });

    return NextResponse.json({
      configured: true,
      servers,
      settings: settings || [],
      memories: memories || [],
      sessions: sessions || [],
      commands: commands || [],
      snapshots: snapshots || [],
      projects: projects || []
    });
  } catch (err) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
