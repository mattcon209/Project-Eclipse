const $ = (s) => document.querySelector(s);
const TOKEN_KEY = "eclipse-token";
const HELP_KEY = "eclipse-help-hidden";

const helpCopy = {
  ladder: {
    title: "Quality ladder",
    body: "Four rungs, one control. Fast is a sketch. Balanced is the daily driver. Quality keeps it. Max is queued and slower. Tap Enhance on a Fast still to promote it without retyping.",
  },
  seed: {
    title: "Seed",
    body: "A seed is the roll of the dice. Same prompt + same seed = the same picture. Seed lock holds it so you can change one word and keep the hallway.",
  },
  paste: {
    title: "Paste a link",
    body: "One paste of a Hugging Face, GitHub, or Civitai link is a complete install. The PC probes size, refuses if the disk can’t take it, downloads, and figures out what the files are. Unknown things land in Inbox — never silent Ready.",
  },
  search: {
    title: "Search this PC",
    body: "Looks on MattsGamingPC for models already installed — Hugging Face cache, Ollama, LM Studio, Downloads, common model folders. Nothing is copied. Ready cards point at the files where they sit. The phone never holds the weights.",
  },
  persona: {
    title: "Persona",
    body: "A short system note that stays on every turn in this thread — a writer’s register, not a content filter. Hollow writer is for game copy. None is the raw model.",
  },
  model: {
    title: "Model on this tab",
    body: "Sorted by what the tab does. Chat remembers the last text model; Image remembers the last picture model. Switching Qwen3 Chat → Image already has the T2I pick. Search this PC if a weight is on disk but missing here.",
  },
};

let token = localStorage.getItem(TOKEN_KEY) || "";
let hiddenHelp = JSON.parse(localStorage.getItem(HELP_KEY) || "{}");
let lastStatus = null;
let libItems = [];

const LATER = {
  audio: ["Audio", "Audio handler is Phase 4. Nothing was faked."],
  video: ["Video", "Video handler is Phase 7. Nothing was faked."],
  talk: ["Talk", "Talk handler is Phase 5. Nothing was faked."],
  edit: ["Edit", "Edit handler is Phase 3. Nothing was faked."],
};

function clock() {
  const d = new Date();
  $("#clock").textContent = d.toTimeString().slice(0, 5);
}
setInterval(clock, 10000);
clock();

async function api(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (token) headers.Authorization = "Bearer " + token;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = res.statusText;
    if (typeof data.reason === "string" && data.reason) msg = data.reason;
    else if (typeof data.error === "string" && data.error) msg = data.error;
    else if (typeof data.detail === "string" && data.detail) msg = data.detail;
    else if (Array.isArray(data.detail) && data.detail[0]) {
      msg = data.detail[0].msg || data.detail[0].message || JSON.stringify(data.detail[0]);
    }
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function showPair(code) {
  $("#view-pair").classList.remove("hidden");
  $("#view-app").classList.add("hidden");
  $("#pair-code").textContent = code || "••••••";
}

function showApp() {
  $("#view-pair").classList.add("hidden");
  $("#view-app").classList.remove("hidden");
}

function applyStatus(s) {
  lastStatus = s;
  const gpu = s.resources?.gpu || {};
  const ram = s.resources?.ram || {};
  const disk = s.resources?.disk || {};
  const eng = $("#chip-engine");
  eng.textContent = s.engine === "running" ? "engine" : "down";
  eng.classList.toggle("live", s.engine === "running");
  if (gpu.available && gpu.vram_used_mb != null) {
    $("#chip-vram").textContent = "vram " + (gpu.vram_used_mb / 1024).toFixed(1);
  } else {
    $("#chip-vram").textContent = "vram n/a";
  }
  $("#project-name").textContent = s.session?.project || "Hollow";
  const mode = s.session?.mode;
  $("#hero-line").textContent = gpu.available
    ? `${gpu.name || "GPU"} · ${gpu.temp_c ?? "—"}° · ${mode ? mode + " warm" : "no mode yet"}`
    : `Engine live on ${s.resources?.hostname || "this box"} · GPU not visible here (will be on MattsGamingPC)`;
  $("#resume-line").textContent = mode ? mode + " still selected" : "tap Image to enter a mode";
  const resume = $("#resume-tile");
  if (resume && mode && ["image", "chat", "audio", "edit", "video", "talk"].includes(mode)) {
    resume.dataset.go = mode;
    const rh = $("#resume-mode");
    if (rh) rh.textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
  }
  $("#jobs-count").textContent = (s.jobs || 0) + " jobs";
  const ready = s.library?.ready;
  if ($("#lib-count")) $("#lib-count").textContent = (ready != null ? ready : 0) + " ready";
  const hostEl = $("#host-name");
  if (hostEl) hostEl.textContent = s.resources?.hostname || "—";
  const gpuEl = $("#gpu-line");
  if (gpuEl) gpuEl.textContent = gpu.available ? gpu.name : "no nvidia-smi in this lab";
  $("#disk-line").textContent = disk.free_gb != null ? disk.free_gb + " GB free" : "—";
  $("#ram-line").textContent = ram.total_mb ? Math.round(ram.used_mb / 1024 * 10) / 10 + " / " + Math.round(ram.total_mb / 1024 * 10) / 10 + " GB" : "RAM —";
  const lad = s.session?.ladder || "balanced";
  document.querySelectorAll(".lad").forEach((b) => b.classList.toggle("on", b.dataset.l === lad));
  const loaded = s.session?.loaded_name || "—";
  $("#filmstock").textContent = `${loaded} · — · seed ${s.session?.seed ?? "—"} · ${lad}`;
  syncPicks();
}

async function boot() {
  const st = await api("/api/status");
  if (!st.paired) {
    showPair(st.pairing?.code);
    return;
  }
  if (!token) {
    showPair(st.pairing?.code);
    $("#pair-hint").textContent = "This browser has no token. Re-pair with the code, or the engine is already bound to another device.";
    return;
  }
  try {
    await api("/api/resources");
    showApp();
    applyStatus(st);
    connectWs();
    refreshJobs();
    refreshLibrary();
    refreshChats();
  } catch (e) {
    token = "";
    localStorage.removeItem(TOKEN_KEY);
    showPair(st.pairing?.code);
  }
}

$("#pair-btn").addEventListener("click", async () => {
  $("#pair-err").textContent = "";
  const typed = $("#pair-input").value.trim() || $("#pair-code").textContent.trim();
  try {
    const r = await api("/api/pair", {
      method: "POST",
      body: JSON.stringify({ code: typed, device_name: "Atelier web / S24+" }),
    });
    token = r.token;
    localStorage.setItem(TOKEN_KEY, token);
    showApp();
    applyStatus(await api("/api/status"));
    connectWs();
    refreshJobs();
    refreshLibrary();
    refreshChats();
  } catch (e) {
    $("#pair-err").textContent = e.message || "Pair failed.";
  }
});

function go(m) {
  const tab = m === "audio" || m === "video" || m === "talk" || m === "edit" ? "chat" : m;
  document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.m === tab));
  ["home", "image", "chat", "library", "jobs"].forEach((id) => {
    const el = $("#screen-" + id);
    if (el) el.classList.toggle("on", id === tab);
  });
  const gen = new Set(["image", "chat", "audio", "edit", "video", "talk", "train"]);
  if (gen.has(m)) {
    api("/api/mode", { method: "POST", body: JSON.stringify({ mode: m }) }).then(async () => {
      applyStatus(await api("/api/status"));
    }).catch(() => {});
  }
  if (m === "jobs") refreshJobs();
  if (m === "library") refreshLibrary();
  if (tab === "chat") refreshChats();
  applyTaskSurface(m);
  fillPicks();
}

document.querySelectorAll(".mode").forEach((b) => b.addEventListener("click", () => go(b.dataset.m)));
document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));

function applyTaskSurface(m) {
  const tm = $("#task-mode");
  if (tm && (m === "chat" || m === "image" || LATER[m])) tm.value = m === "edit" ? "chat" : m;
  const later = $("#later-empty");
  const log = $("#chat-log");
  const threads = $("#chat-threads");
  const prompt = $("#screen-chat .prompt");
  const live = m === "chat" || !LATER[m];
  if (later) later.classList.toggle("hidden", live);
  if (log) log.classList.toggle("hidden", !live);
  if (threads) threads.classList.toggle("hidden", !live);
  if (prompt) prompt.classList.toggle("hidden", !live);
  if (!live && LATER[m]) {
    const pair = LATER[m];
    if ($("#later-title")) $("#later-title").textContent = pair[0];
    if ($("#later-body")) $("#later-body").textContent = pair[1];
  }
}

function fillPicks() {
  const by = (lastStatus && lastStatus.session && lastStatus.session.by_mode) || {};
  const loaded = (lastStatus && lastStatus.session && lastStatus.session.loaded) || "";
  const mode = lastStatus && lastStatus.session && lastStatus.session.mode;
  const ready = (libItems || []).filter((i) => i.state === "ready");
  const chat = $("#chat-model");
  if (chat) {
    const text = ready.filter((i) => i.modality === "text");
    const cur = (by.chat && by.chat.id) || (mode === "chat" ? loaded : "") || chat.value;
    chat.innerHTML = '<option value="">text model…</option>' + text.map((i) => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.ollama_name || i.name)}</option>`).join("");
    if (cur && [...chat.options].some((o) => o.value === cur)) chat.value = cur;
  }
  const img = $("#image-model");
  if (img) {
    const pics = ready.filter((i) => i.modality === "image" || i.modality === "video");
    const cur = (by.image && by.image.id) || (mode === "image" ? loaded : "") || img.value;
    img.innerHTML = '<option value="">image model…</option>' + pics.map((i) => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join("");
    if (cur && [...img.options].some((o) => o.value === cur)) img.value = cur;
  }
}

function syncPicks() {
  const sess = lastStatus && lastStatus.session;
  if (!sess) return;
  const by = sess.by_mode || {};
  const loaded = sess.loaded || "";
  const chat = $("#chat-model");
  if (chat && chat.options.length) {
    const id = (by.chat && by.chat.id) || (sess.mode === "chat" ? loaded : "");
    if (id && [...chat.options].some((o) => o.value === id)) chat.value = id;
  }
  const img = $("#image-model");
  if (img && img.options.length) {
    const id = (by.image && by.image.id) || (sess.mode === "image" ? loaded : "");
    if (id && [...img.options].some((o) => o.value === id)) img.value = id;
  }
}

async function pickUse(sel) {
  const id = sel && sel.value;
  if (!id) return;
  const errChat = $("#chat-err");
  const errImg = $("#image-err");
  try {
    const used = await api("/api/library/" + id + "/use", { method: "POST", body: "{}" });
    applyStatus(await api("/api/status"));
    const mod = used.record && used.record.modality;
    if (mod === "image" || mod === "video") go("image");
    if (mod === "text") go("chat");
  } catch (e) {
    const msg = e.message || "Use failed.";
    if (errChat) errChat.textContent = msg;
    if (errImg) errImg.textContent = msg;
  }
}

if ($("#chat-model")) $("#chat-model").addEventListener("change", () => pickUse($("#chat-model")));
if ($("#image-model")) $("#image-model").addEventListener("change", () => pickUse($("#image-model")));
if ($("#task-mode")) {
  $("#task-mode").addEventListener("change", () => {
    const m = $("#task-mode").value;
    go(m);
  });
}

document.querySelectorAll(".lad").forEach((b) => {
  b.addEventListener("click", async () => {
    await api("/api/ladder", { method: "POST", body: JSON.stringify({ ladder: b.dataset.l }) });
    document.querySelectorAll(".lad").forEach((x) => x.classList.toggle("on", x === b));
  });
});

$("#make").addEventListener("click", async () => {
  const err = $("#image-err");
  if (err) err.textContent = "";
  const prompt = $("#prompt").value.trim();
  try {
    const job = await api("/api/make", { method: "POST", body: JSON.stringify({ prompt }) });
    go("jobs");
    renderJobs([job, ...((await api("/api/jobs")).jobs || []).filter((j) => j.id !== job.id)]);
  } catch (e) {
    if (err) err.textContent = e.message || "Make failed.";
  }
});

async function refreshJobs() {
  try {
    const r = await api("/api/jobs");
    renderJobs(r.jobs || []);
  } catch (_) {}
}

function renderJobs(jobs) {
  const el = $("#job-list");
  if (!jobs.length) {
    el.innerHTML = '<p class="faint">No jobs yet. Make will queue an honest blocked job until a model is installed.</p>';
    return;
  }
  el.innerHTML = jobs
    .map((j) => {
      const last = (j.log && j.log[j.log.length - 1] && j.log[j.log.length - 1].line) || "";
      const canCancel = j.state === "queued" || j.state === "running" || j.state === "downloading";
      const cancel = canCancel
        ? `<button type="button" class="ghost cancel" data-id="${escapeHtml(j.id)}">Cancel</button>`
        : "";
      return `<article class="job"><div class="st"><span>${escapeHtml(j.state)} · ${escapeHtml(j.kind)}</span>${cancel}</div><h3>${escapeHtml(j.title)}</h3><p>${escapeHtml(last)}</p></article>`;
    })
    .join("");
  el.querySelectorAll(".cancel").forEach((b) => {
    b.addEventListener("click", async () => {
      try {
        await api("/api/jobs/" + b.dataset.id + "/cancel", { method: "POST", body: "{}" });
        await refreshJobs();
      } catch (e) {
        b.textContent = e.message || "Failed";
      }
    });
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("#recal").addEventListener("click", async () => {
  const err = $("#lib-err");
  if (err) err.textContent = "";
  try {
    await api("/api/calibrate", { method: "POST" });
    applyStatus(await api("/api/status"));
    if (err) err.textContent = "Calibrated.";
  } catch (e) {
    if (err) err.textContent = e.message || "Calibrate failed.";
  }
});

function openHelp(key) {
  if (hiddenHelp[key]) return;
  const copy = helpCopy[key];
  if (!copy) return;
  $("#help-title").textContent = copy.title;
  $("#help-body").textContent = copy.body;
  $("#help").dataset.key = key;
  $("#help").classList.add("on");
}
$("#q-ladder").addEventListener("click", (e) => {
  e.stopPropagation();
  openHelp("ladder");
});
$("#q-seed").addEventListener("click", (e) => {
  e.stopPropagation();
  openHelp("seed");
});
$("#q-paste").addEventListener("click", (e) => {
  e.stopPropagation();
  openHelp("paste");
});
$("#q-search").addEventListener("click", (e) => {
  e.stopPropagation();
  openHelp("search");
});
$("#help-ok").addEventListener("click", () => $("#help").classList.remove("on"));
$("#help-hide").addEventListener("click", () => {
  hiddenHelp[$("#help").dataset.key] = true;
  localStorage.setItem(HELP_KEY, JSON.stringify(hiddenHelp));
  $("#help").classList.remove("on");
});

async function refreshLibrary() {
  try {
    const r = await api("/api/library");
    libItems = r.items || [];
    renderLibrary(libItems);
    fillPicks();
  } catch (_) {}
}

function renderLibrary(items) {
  const el = $("#lib-list");
  if (!el) return;
  if (!items.length) {
    el.innerHTML = '<p class="faint">Empty. Search this PC for models already on disk, or paste a link. Unknown files go to Inbox, never silent Ready.</p>';
    return;
  }
  el.innerHTML = items
    .map((it) => {
      const st = (it.state || "—").toUpperCase();
      const mod = (it.modality || "unknown").toUpperCase();
      const gb = it.bytes != null ? (it.bytes / 1024 ** 3).toFixed(2) + " GB" : "size ?";
      const action = it.state === "ready" ? `<button class="ghost use" data-id="${it.id}" type="button">Use</button>` : "";
      return `<article class="job"><div class="st">${st} · ${mod}</div><h3>${escapeHtml(it.name || "untitled")}</h3><p>${escapeHtml(gb)} · ${escapeHtml(it.notes || it.format || "")}</p>${action}</article>`;
    })
    .join("");
  el.querySelectorAll(".use").forEach((b) => {
    b.addEventListener("click", async () => {
      const err = $("#lib-err");
      if (err) err.textContent = "";
      try {
        const used = await api("/api/library/" + b.dataset.id + "/use", { method: "POST", body: "{}" });
        applyStatus(await api("/api/status"));
        const name = used.record?.name || "model";
        const fit = used.fit || {};
        let msg = `Loaded ${name}.`;
        if (used.attached === "lora") msg = `Attached LoRA ${name}.`;
        else if (fit.fits === false) msg = fit.reason || `${name} won’t fit VRAM.`;
        else if ((used.record?.modality || "") === "text") msg = `Loaded ${name}.`;
        if (err) err.textContent = msg;
        const imageErr = $("#image-err");
        if (imageErr && used.record?.modality !== "text") imageErr.textContent = msg;
        const mod = used.record?.modality;
        if (mod === "image" || mod === "video") go("image");
        if (mod === "text") go("chat");
      } catch (e) {
        if (err) err.textContent = e.message || "Use failed.";
      }
    });
  });
}

async function searchThisPc() {
  const btn = $("#lib-search");
  const err = $("#lib-err");
  if (!btn || !err) return;
  err.textContent = "";
  btn.disabled = true;
  btn.textContent = "Searching…";
  try {
    const r = await api("/api/library/search", { method: "POST", body: JSON.stringify({}) });
    await refreshLibrary();
    applyStatus(await api("/api/status"));
    const n = r.added || 0;
    const ready = r.ready || 0;
    const found = r.found || 0;
    const roots = (r.roots || []).length;
    if (found || ready) {
      err.textContent = `Found ${found} · added ${n} · ${ready} Ready. Looked in ${roots} folder(s). Files stayed on the PC.`;
    } else {
      err.textContent = `Looked in ${roots} folder(s), found 0. Ollama blobs and LM Studio paths are included. If they’re on another drive, set ECLIPSE_SCAN_ROOTS.`;
    }
  } catch (e) {
    const d = e.data || {};
    err.textContent = d.reason || e.message || "Search failed. Pull latest and restart the engine.";
  } finally {
    btn.disabled = false;
    btn.textContent = "Search this PC";
  }
}

const libSearchBtn = $("#lib-search");
if (libSearchBtn) libSearchBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  searchThisPc();
});

$("#lib-add").addEventListener("click", async () => {
  $("#lib-err").textContent = "";
  const url = $("#lib-url").value.trim();
  if (!url) {
    $("#lib-err").textContent = "Paste a link, or Search this PC.";
    return;
  }
  try {
    const r = await api("/api/library/acquire", { method: "POST", body: JSON.stringify({ url }) });
    if (r.needs_confirm) {
      const ok = window.confirm(r.reason || "Large download. Confirm?");
      if (!ok) return;
      await api("/api/library/acquire", { method: "POST", body: JSON.stringify({ url, confirm: true }) });
    }
    await refreshLibrary();
  } catch (e) {
    const d = e.data || {};
    $("#lib-err").textContent = d.reason || e.message || "Install failed.";
  }
});


let currentThread = null;
let chatBusy = false;

function chatModelLabel() {
  const sess = lastStatus && lastStatus.session;
  if (!sess) return "";
  const by = (sess.by_mode && sess.by_mode.chat) || {};
  if (by.name) return by.name;
  if (sess.mode === "chat") return sess.loaded_name || "";
  return sess.loaded_name || "";
}

function renderTurns(turns) {
  const el = $("#chat-log");
  if (!el) return;
  if (!turns || !turns.length) {
    el.innerHTML = '<div class="empty-frame" id="chat-empty"><span>No thread yet</span><small>Use a Ready text model in Library, then Send.</small></div>';
    return;
  }
  el.innerHTML = turns
    .map((t) => {
      const who = t.role === "user" ? "you" : t.role === "system" ? "persona" : (t.model_name || chatModelLabel() || "model");
      return `<article class="turn ${escapeHtml(t.role)}"><div class="who">${escapeHtml(who)}</div><div class="body">${escapeHtml(t.text || "")}</div></article>`;
    })
    .join("");
  el.scrollTop = el.scrollHeight;
}

function renderThreadStrip(threads) {
  const el = $("#chat-threads");
  if (!el) return;
  if (!threads.length) {
    el.innerHTML = "";
    return;
  }
  el.innerHTML = threads
    .map((t) => {
      const on = t.id === currentThread ? " on" : "";
      return `<button type="button" class="chip-thread${on}" data-id="${escapeHtml(t.id)}">${escapeHtml(t.title || "New chat")}</button>`;
    })
    .join("");
  el.querySelectorAll(".chip-thread").forEach((b) => {
    b.addEventListener("click", () => openThread(b.dataset.id));
  });
}

async function openThread(id) {
  currentThread = id;
  try {
    const th = await api("/api/chats/" + id);
    currentThread = th.id;
    if (th.persona_id && $("#chat-persona")) $("#chat-persona").value = th.persona_id;
    renderTurns(th.turns || []);
    const list = await api("/api/chats");
    renderThreadStrip(list.threads || []);
  } catch (e) {
    const err = $("#chat-err");
    if (err) err.textContent = e.message || "Couldn’t open thread.";
  }
}

async function refreshChats() {
  try {
    const q = ($("#chat-find") && $("#chat-find").value.trim()) || "";
    const path = q ? "/api/chats?q=" + encodeURIComponent(q) : "/api/chats";
    const r = await api(path);
    renderThreadStrip(r.threads || []);
    if (!currentThread && r.threads && r.threads[0]) {
      await openThread(r.threads[0].id);
    } else if (currentThread) {
      renderThreadStrip(r.threads || []);
    }
    const personas = await api("/api/personas");
    const sel = $("#chat-persona");
    if (sel && sel.dataset.ready !== "1") {
      sel.innerHTML = (personas.personas || [])
        .map((p) => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`)
        .join("");
      sel.dataset.ready = "1";
    }
  } catch (_) {}
}

function appendLocalTurn(role, text, extra) {
  const el = $("#chat-log");
  if (!el) return null;
  if ($("#chat-empty")) el.innerHTML = "";
  const art = document.createElement("article");
  art.className = "turn " + role;
  const who = role === "user" ? "you" : extra || chatModelLabel() || "model";
  art.innerHTML = `<div class="who">${escapeHtml(who)}</div><div class="body"></div>`;
  art.querySelector(".body").textContent = text || "";
  el.appendChild(art);
  el.scrollTop = el.scrollHeight;
  return art;
}

async function sendChat() {
  const err = $("#chat-err");
  if (err) err.textContent = "";
  const input = $("#chat-input");
  const prompt = (input && input.value) || "";
  if (!prompt.trim()) {
    if (err) err.textContent = "Type something first.";
    return;
  }
  if (chatBusy) return;
  chatBusy = true;
  const stop = $("#chat-stop");
  if (stop) stop.classList.add("on");
  if (input) input.value = "";
  appendLocalTurn("user", prompt);
  const asst = appendLocalTurn("assistant", "");
  const bodyEl = asst ? asst.querySelector(".body") : null;
  const tid = currentThread || "new";
  const persona = ($("#chat-persona") && $("#chat-persona").value) || "none";
  try {
    const headers = { "Content-Type": "application/json", Accept: "text/event-stream" };
    if (token) headers.Authorization = "Bearer " + token;
    const res = await fetch("/api/chats/" + tid + "/send", {
      method: "POST",
      headers,
      body: JSON.stringify({ prompt, persona_id: persona }),
    });
    const ctype = res.headers.get("content-type") || "";
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.reason || data.detail || res.statusText);
    }
    if (ctype.indexOf("text/event-stream") >= 0 && res.body) {
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      let acc = "";
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buf += dec.decode(chunk.value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const part of parts) {
          const line = part.replace(/^data:\s*/, "").trim();
          if (!line) continue;
          let ev;
          try { ev = JSON.parse(line); } catch (_) { continue; }
          if (ev.type === "user" && ev.thread && ev.thread.id) currentThread = ev.thread.id;
          if (ev.type === "token") {
            acc += ev.text || "";
            if (bodyEl) bodyEl.textContent = acc;
            if (ev.ttft_ms != null && asst) {
              const whoEl = asst.querySelector(".who");
              const name = chatModelLabel() || "model";
              if (whoEl && whoEl.dataset.ttft !== "1") {
                whoEl.textContent = name + (ev.ttft_ms < 1000 ? " · " + ev.ttft_ms + "ms" : " · " + (ev.ttft_ms / 1000).toFixed(1) + "s");
                whoEl.dataset.ttft = "1";
              }
            }
            const log = $("#chat-log");
            if (log) log.scrollTop = log.scrollHeight;
          }
          if (ev.type === "done") {
            if (ev.thread && ev.thread.id) currentThread = ev.thread.id;
            if (bodyEl) bodyEl.textContent = (ev.assistant && ev.assistant.text) || acc;
            const whoEl = asst && asst.querySelector(".who");
            if (whoEl) {
              const name = (ev.assistant && ev.assistant.model_name) || chatModelLabel() || "model";
              const ms = ev.ttft_ms;
              whoEl.textContent = ms == null ? name : name + (ms < 1000 ? " · " + ms + "ms" : " · " + (ms / 1000).toFixed(1) + "s");
            }
            if (ev.ok === false && err) err.textContent = ev.reason || "";
          }
        }
      }
    } else {
      const data = await res.json();
      if (data.thread && data.thread.id) currentThread = data.thread.id;
      if (bodyEl) bodyEl.textContent = (data.assistant && data.assistant.text) || "";
      const whoEl = asst && asst.querySelector(".who");
      if (whoEl) whoEl.textContent = (data.assistant && data.assistant.model_name) || chatModelLabel() || "model";
      if (data.ok === false && err) err.textContent = data.reason || "";
    }
    await refreshChats();
  } catch (e) {
    if (err) err.textContent = e.message || "Send failed.";
    if (bodyEl && !bodyEl.textContent) bodyEl.textContent = e.message || "Send failed.";
  } finally {
    chatBusy = false;
    if (stop) stop.classList.remove("on");
  }
}

$("#chat-send").addEventListener("click", () => sendChat());
$("#chat-new").addEventListener("click", async () => {
  const err = $("#chat-err");
  if (err) err.textContent = "";
  try {
    const persona = ($("#chat-persona") && $("#chat-persona").value) || "none";
    const th = await api("/api/chats", { method: "POST", body: JSON.stringify({ persona_id: persona }) });
    currentThread = th.id;
    renderTurns([]);
    await refreshChats();
  } catch (e) {
    if (err) err.textContent = e.message || "Couldn’t start a thread.";
  }
});
$("#chat-stop").addEventListener("click", () => {
  const tid = currentThread || "new";
  api("/api/chats/" + tid + "/stop", { method: "POST", body: "{}" }).catch(() => {});
});
$("#q-persona").addEventListener("click", (e) => {
  e.stopPropagation();
  openHelp("persona");
});
if ($("#q-model")) {
  $("#q-model").addEventListener("click", (e) => {
    e.stopPropagation();
    openHelp("model");
  });
}
if ($("#chat-find")) {
  $("#chat-find").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      refreshChats();
    }
  });
}

let wsHandle = null;
let wsTimer = null;
function connectWs() {
  if (!token) return;
  if (wsHandle && (wsHandle.readyState === 0 || wsHandle.readyState === 1)) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws?token=${encodeURIComponent(token)}`);
  wsHandle = ws;
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "status") applyStatus(msg.payload);
    } catch (_) {}
  };
  ws.onclose = () => {
    if (wsHandle === ws) wsHandle = null;
    const app = $("#view-app");
    if (token && app && !app.classList.contains("hidden")) {
      clearTimeout(wsTimer);
      wsTimer = setTimeout(connectWs, 2500);
    }
  };
}

function onEnter(sel, btn) {
  const el = $(sel);
  if (!el) return;
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const b = $(btn);
      if (b) b.click();
    }
  });
}
onEnter("#pair-input", "#pair-btn");
onEnter("#lib-url", "#lib-add");
onEnter("#prompt", "#make");
onEnter("#chat-input", "#chat-send");

boot().catch((e) => {
  $("#pair-hint").textContent = "Cannot reach the engine. Is it running on this LAN?";
  showPair("");
});
