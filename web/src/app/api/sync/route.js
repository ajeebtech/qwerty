import { NextResponse } from "next/server";
import { supabase } from "../../lib/supabase";

export async function POST(req) {
  if (!supabase) {
    return NextResponse.json({ error: "Supabase not configured" }, { status: 400 });
  }

  try {
    const payload = await req.json();
    const { sessions, commands, memories, settings, snapshots, projects, brain_versions } = payload;

    const promises = [];

    if (sessions && sessions.length > 0) {
      promises.push(supabase.from("sessions").upsert(sessions));
    }
    if (commands && commands.length > 0) {
      promises.push(supabase.from("commands").upsert(commands));
    }
    if (memories && memories.length > 0) {
      promises.push(supabase.from("ai_memory").upsert(memories));
    }
    if (settings && settings.length > 0) {
      promises.push(supabase.from("settings").upsert(settings));
    }
    if (snapshots && snapshots.length > 0) {
      promises.push(supabase.from("server_snapshots").upsert(snapshots));
    }
    if (projects && projects.length > 0) {
      promises.push(supabase.from("projects").upsert(projects));
    }
    if (brain_versions && brain_versions.length > 0) {
      promises.push(supabase.from("brain_versions").upsert(brain_versions));
    }

    const results = await Promise.all(promises);

    for (const res of results) {
      if (res.error) {
        throw new Error(res.error.message);
      }
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
