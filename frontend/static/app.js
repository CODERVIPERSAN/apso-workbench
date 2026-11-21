/** APSO Agent Workbench — Cursor-inspired shell (original UI; not Cursor source). */

const state = {
  mode: "agent", // ask | agent | plan
  hitlId: null,
  tools: [],
  live: {},
  sessionId: localStorage.getItem("apso_session_id") || "",
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (s) =>
  String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

async function api(path, opts) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function clearEmpty() {
  const t = $("#transcript");
  if (t.querySelector(".empty")) t.innerHTML = "";
}

function addMsg(role, who, text) {
  clearEmpty();
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.innerHTML = `<div class="who">${esc(who)}</div><div class="body">${esc(text)}</div>`;
  $("#transcript").appendChild(el);
  $("#transcript").scrollTop = $("#transcript").scrollHeight;
}

function addToolCard(agent, tool, args, result, running) {
  clearEmpty();
  const id = `tool-${agent}-${tool}-${Date.now()}`;
  const el = document.createElement("div");
  el.className = `tool-card ${running ? "running" : "done"}`;
  el.id = id;
  el.innerHTML = `
    <div class="th"><span>⚒</span><b>${esc(tool)}</b><span>${esc(agent)}</span></div>
    <div class="tb">${esc(JSON.stringify(args || {}, null, 0).slice(0, 200))}${
      result !== undefined ? "\n→ " + esc(JSON.stringify(result).slice(0, 280)) : ""
    }</div>`;
  $("#transcript").appendChild(el);
  $("#transcript").scrollTop = $("#transcript").scrollHeight;
  return id;
}

function setLive(agent, status) {
  state.live[agent] = status;
  const host = $("#live-agents");
  host.innerHTML = Object.entries(state.live)
    .map(([n, s]) => `<span class="pill ${s === "running" ? "run" : "on"}">${n} · ${s}</span>`)
    .join("") || "Idle";
}

function handleEvent(ev) {
  if (ev.type === "session" && ev.session_id) {
    state.sessionId = ev.session_id;
    localStorage.setItem("apso_session_id", ev.session_id);
  } else if (ev.type === "status") {
    $("#panel-meta").textContent = ev.message || "";
  } else if (ev.type === "agent_start") {
    // Status only — do not add a chat bubble (avoids "Here to help" + reply spam)
    setLive(ev.agent, "running");
  } else if (ev.type === "agent_thinking") {
    setLive(ev.agent, "running");
  } else if (ev.type === "agent_message") {
    // Skip — final answer comes once via agent_done
  } else if (ev.type === "text") {
    addMsg("agent", "orchestrator", ev.text);
  } else if (ev.type === "tool_start") {
    addToolCard(ev.agent || "agent", ev.tool, ev.args, undefined, true);
    state.tools.push(ev.tool);
    $("#tool-trail").textContent = [...new Set(state.tools)].join("\n");
  } else if (ev.type === "tool_done") {
    addToolCard(ev.agent || "agent", ev.tool, ev.args || {}, ev.result, false);
    state.tools.push(ev.tool);
    $("#tool-trail").textContent = [...new Set(state.tools)].join("\n");
  } else if (ev.type === "agent_done") {
    setLive(ev.agent, "done");
    if (ev.summary) addMsg("agent", ev.agent, ev.summary);
  } else if (ev.type === "plan") {
    addMsg("agent", "orchestrator · plan", `Agents: ${(ev.agents || []).join(" → ")}`);
  } else if (ev.type === "hitl_gate") {
    state.hitlId = ev.hitl_id;
    $("#hitl").classList.remove("hidden");
    $("#hitl-msg").textContent = ev.message || "Needs your OK before we change anything";
    addMsg("agent", "needs your OK", ev.message || "Please review and Accept to apply.");
  } else if (ev.type === "error") {
    addMsg("agent", "error", ev.text);
  } else if (ev.type === "done" && ev.tools_used) {
    addMsg("agent", "orchestrator", `Done. Tools: ${[...new Set(ev.tools_used)].join(", ") || "—"}`);
  }
}

async function sendPrompt(text) {
  if (!text.trim()) return;
  state.tools = [];
  addMsg("user", "You", text);
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: text,
      mode: state.mode,
      auto: true,
      session_id: state.sessionId || null,
    }),
  });
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop();
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      handleEvent(JSON.parse(line.slice(5).trim()));
    }
  }
  refresh();
}

function setMode(mode) {
  state.mode = mode;
  $$(".mode").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  $("#mode-tag").textContent = mode[0].toUpperCase() + mode.slice(1);
  const labels = {
    ask: "Ask · read-only",
    agent: "Agent · multi-agent swarm",
    plan: "Plan · orchestrator plan only",
  };
  $("#panel-meta").textContent = labels[mode];
}

async function refresh() {
  const [status, health, agents, incidents] = await Promise.all([
    api("/api/status"),
    api("/api/health"),
    api("/api/agents"),
    api("/api/incidents"),
  ]);
  $("#kpis").innerHTML = `
    <span>${status.incidents} INC</span>
    <span>${status.agents_active} agents</span>
    <span>${status.pending} HITL</span>`;
  $("#llm-pill").textContent = health.connectors.model
    ? "Ollama · llama3.2"
    : "Model offline";
  $("#connectors").innerHTML = Object.entries(health.connectors)
    .map(([k, v]) => `<span class="pill ${v ? "on" : ""}">${k}${v ? " ✓" : ""}</span>`)
    .join("");
  $("#agent-list").innerHTML = agents
    .map(
      (a) =>
        `<div class="agent-row">${a.name}<span class="st">${a.status}</span><div style="color:#666;font-size:10px">${a.description || a.stage || ""}</div></div>`
    )
    .join("");
  $("#inc-list").innerHTML = incidents
    .map(
      (i) =>
        `<div class="inc-row" data-inc="${i.number}"><b>${i.number}</b> · P${i.priority}<div style="color:#888">${esc(i.short_description).slice(0, 60)}</div></div>`
    )
    .join("");
  $$(".inc-row").forEach((el) => {
    el.onclick = () => {
      setMode("agent");
      sendPrompt(`Investigate ${el.dataset.inc}`);
    };
  });
}

// Activity bar panels
$$(".act[data-panel]").forEach((btn) => {
  btn.onclick = () => {
    $$(".act[data-panel]").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const p = btn.dataset.panel;
    $("#side-chat").classList.toggle("hidden", p !== "chat");
    $("#side-agents").classList.toggle("hidden", p !== "agents");
    $("#side-incidents").classList.toggle("hidden", p !== "incidents" && p !== "gov" && p !== "knowledge");
    if (p === "gov" || p === "knowledge") $("#side-incidents").classList.add("hidden");
  };
});

$$(".mode").forEach((b) => {
  b.onclick = () => setMode(b.dataset.mode);
});

$("#send").onclick = () => {
  const v = $("#prompt").value;
  $("#prompt").value = "";
  sendPrompt(v);
};
$("#prompt").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#send").click();
  }
});

$("#btn-new").onclick = () => {
  $("#transcript").innerHTML = `<div class="empty"><h1>New Agent</h1><p>Ask, Plan, or Agent — Cursor-style modes for APSO.</p><p class="hint"><code>Investigate INC5668817</code></p></div>`;
  state.live = {};
  $("#live-agents").textContent = "Idle";
  $("#tool-trail").textContent = "";
  $("#hitl").classList.add("hidden");
};

$("#hitl-apply").onclick = async () => {
  if (!state.hitlId) return;
  const res = await api(`/api/hitl/${state.hitlId}/approve`, { method: "POST" });
  addMsg("agent", "checkpoint · Accept", JSON.stringify(res).slice(0, 400));
  $("#hitl").classList.add("hidden");
  refresh();
};
$("#hitl-reject").onclick = async () => {
  if (!state.hitlId) return;
  await api(`/api/hitl/${state.hitlId}/reject`, { method: "POST" });
  $("#hitl").classList.add("hidden");
  addMsg("agent", "checkpoint", "Rejected");
};
$("#btn-kill").onclick = async () => {
  await api("/api/governance/kill-switch?on=true", { method: "POST" });
  refresh();
};
$("#btn-unkill").onclick = async () => {
  await api("/api/governance/kill-switch?on=false", { method: "POST" });
  refresh();
};

setMode("agent");
refresh();
