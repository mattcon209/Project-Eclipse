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
};

let token = localStorage.getItem(TOKEN_KEY) || "";
let hiddenHelp = JSON.parse(localStorage.getItem(HELP_KEY) || "{}");
let lastStatus = null;

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
    const err = new Error(data.error || data.detail || res.statusText);
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
  } catch (e) {
    $("#pair-err").textContent = e.message || "Pair failed.";
  }
});

function go(m) {
  document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.m === m));
  ["home", "image", "library", "jobs"].forEach((id) => {
    const el = $("#screen-" + id);
    if (el) el.classList.toggle("on", id === m);
  });
  const gen = new Set(["image", "chat", "audio", "edit", "video", "talk", "train"]);
  if (gen.has(m)) {
    api("/api/mode", { method: "POST", body: JSON.stringify({ mode: m }) }).catch(() => {});
  }
  if (m === "jobs") refreshJobs();
  if (m === "library") refreshLibrary();
}

document.querySelectorAll(".mode").forEach((b) => b.addEventListener("click", () => go(b.dataset.m)));
document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));

document.querySelectorAll(".lad").forEach((b) => {
  b.addEventListener("click", async () => {
    await api("/api/ladder", { method: "POST", body: JSON.stringify({ ladder: b.dataset.l }) });
    document.querySelectorAll(".lad").forEach((x) => x.classList.toggle("on", x === b));
  });
});

$("#make").addEventListener("click", async () => {
  const prompt = $("#prompt").value.trim();
  const job = await api("/api/make", { method: "POST", body: JSON.stringify({ prompt }) });
  go("jobs");
  renderJobs([job, ...((await api("/api/jobs")).jobs || []).filter((j) => j.id !== job.id)]);
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
      return `<article class="job"><div class="st">${j.state} · ${j.kind}</div><h3>${escapeHtml(j.title)}</h3><p>${escapeHtml(last)}</p></article>`;
    })
    .join("");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("#recal").addEventListener("click", async () => {
  await api("/api/calibrate", { method: "POST" });
  applyStatus(await api("/api/status"));
});

function openHelp(key) {
  if (hiddenHelp[key]) return;
  $("#help-title").textContent = helpCopy[key].title;
  $("#help-body").textContent = helpCopy[key].body;
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
    renderLibrary(r.items || []);
  } catch (_) {}
}

function renderLibrary(items) {
  const el = $("#lib-list");
  if (!el) return;
  if (!items.length) {
    el.innerHTML = '<p class="faint">Empty. Paste a link — Ready cards land here. Unknown files go to Inbox, never silent Ready.</p>';
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
      const used = await api("/api/library/" + b.dataset.id + "/use", { method: "POST", body: "{}" });
      applyStatus(await api("/api/status"));
      const mod = used.record?.modality;
      if (mod === "image" || mod === "video") go("image");
    });
  });
}

$("#lib-add").addEventListener("click", async () => {
  $("#lib-err").textContent = "";
  const url = $("#lib-url").value.trim();
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

function connectWs() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws?token=${encodeURIComponent(token)}`);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "status") applyStatus(msg.payload);
    } catch (_) {}
  };
}

boot().catch((e) => {
  $("#pair-hint").textContent = "Cannot reach the engine. Is it running on this LAN?";
  showPair("");
});
