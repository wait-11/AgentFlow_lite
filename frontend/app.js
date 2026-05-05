const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8010" : "";

const state = {
  tools: [],
  models: [],
  runs: [],
  activeRun: null,
  eventSource: null,
};

const els = {
  healthBadge: document.querySelector("#healthBadge"),
  modelSelect: document.querySelector("#modelSelect"),
  baseUrlInput: document.querySelector("#baseUrlInput"),
  toolGrid: document.querySelector("#toolGrid"),
  runForm: document.querySelector("#runForm"),
  runButton: document.querySelector("#runButton"),
  queryInput: document.querySelector("#queryInput"),
  maxStepsInput: document.querySelector("#maxStepsInput"),
  maxTimeInput: document.querySelector("#maxTimeInput"),
  maxTokensInput: document.querySelector("#maxTokensInput"),
  temperatureInput: document.querySelector("#temperatureInput"),
  verboseInput: document.querySelector("#verboseInput"),
  activeRunId: document.querySelector("#activeRunId"),
  activeStatus: document.querySelector("#activeStatus"),
  resultOutput: document.querySelector("#resultOutput"),
  timeline: document.querySelector("#timeline"),
  eventCount: document.querySelector("#eventCount"),
  historyList: document.querySelector("#historyList"),
  refreshButton: document.querySelector("#refreshButton"),
  historyRefreshButton: document.querySelector("#historyRefreshButton"),
  exampleButton: document.querySelector("#exampleButton"),
  selectBasicTools: document.querySelector("#selectBasicTools"),
  copyResultButton: document.querySelector("#copyResultButton"),
  toast: document.querySelector("#toast"),
};

const terminalStatuses = new Set(["completed", "failed", "cancelled"]);
const sseEvents = ["queued", "started", "solver_constructing", "solver_ready", "completed", "failed", "error"];
const statusFromEvent = {
  queued: "queued",
  started: "running",
  solver_constructing: "running",
  solver_ready: "running",
  completed: "completed",
  failed: "failed",
};

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function requestJson(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail || `HTTP ${response.status}`);
  }

  return response.json();
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.remove("is-visible");
  }, 2600);
}

function setHealth(status, label) {
  els.healthBadge.className = `health-badge ${status}`;
  els.healthBadge.innerHTML = `<span class="status-dot"></span>${label}`;
}

function setStatus(status) {
  els.activeStatus.textContent = status;
  els.activeStatus.className = `status-pill is-${status}`;
}

function formatTime(value) {
  if (!value) return "--";
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function summarizeOutput(run) {
  if (!run) return "提交任务后，结果会显示在这里。";
  if (run.error) return run.error;
  if (!run.output) return "任务正在运行，等待最终输出。";
  return run.output.direct_output || run.output.final_output || JSON.stringify(run.output, null, 2);
}

function selectedToolNames() {
  return [...els.toolGrid.querySelectorAll("input[type='checkbox']:checked")].map((input) => input.value);
}

function renderModels() {
  if (!state.models.length) {
    els.modelSelect.innerHTML = `<option value="dashscope">dashscope</option>`;
    return;
  }

  els.modelSelect.innerHTML = state.models
    .map((model) => {
      const label = `${model.name} - ${model.provider}`;
      return `<option value="${escapeHtml(model.name)}" data-base-url="${model.supports_base_url}">${escapeHtml(label)}</option>`;
    })
    .join("");
}

function renderTools() {
  if (!state.tools.length) {
    els.toolGrid.innerHTML = `<div class="empty-state">工具列表加载中</div>`;
    return;
  }

  els.toolGrid.innerHTML = state.tools
    .map((tool, index) => {
      const checked = index === 0 ? "checked" : "";
      return `
        <label class="tool-card ${checked ? "is-selected" : ""}">
          <input type="checkbox" value="${escapeHtml(tool.name)}" ${checked} />
          <span class="tool-name">${escapeHtml(tool.display_name)}</span>
          <p class="tool-description">${escapeHtml(tool.description)}</p>
          <span class="tool-meta">${escapeHtml(tool.name)} / ${escapeHtml(tool.recommended_engine)}</span>
        </label>
      `;
    })
    .join("");

  els.toolGrid.querySelectorAll(".tool-card input").forEach((input) => {
    input.addEventListener("change", () => {
      input.closest(".tool-card").classList.toggle("is-selected", input.checked);
    });
  });
}

function renderTimeline(events = []) {
  els.eventCount.textContent = `${events.length} events`;

  if (!events.length) {
    els.timeline.innerHTML = `<li class="empty-state">暂无事件</li>`;
    return;
  }

  els.timeline.innerHTML = events
    .map(
      (event) => `
        <li class="timeline-item is-${event.type}">
          <span class="timeline-marker"></span>
          <div>
            <div class="timeline-title">
              <span class="timeline-type">${escapeHtml(event.type)}</span>
              <span class="timeline-time">${formatTime(event.timestamp)}</span>
            </div>
            <p class="timeline-message">${escapeHtml(event.message)}</p>
          </div>
        </li>
      `,
    )
    .join("");
  els.timeline.scrollTop = els.timeline.scrollHeight;
}

function renderActiveRun(run) {
  state.activeRun = run;
  els.activeRunId.textContent = run?.run_id || "尚未创建";
  setStatus(run?.status || "idle");
  els.resultOutput.textContent = summarizeOutput(run);
  renderTimeline(run?.events || []);
}

function renderHistory() {
  const sortedRuns = [...state.runs].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  if (!sortedRuns.length) {
    els.historyList.innerHTML = `<div class="empty-state">还没有任务记录</div>`;
    return;
  }

  els.historyList.innerHTML = sortedRuns
    .map(
      (run) => `
        <article class="history-row">
          <div class="history-query">
            <strong>${escapeHtml(run.request.query)}</strong>
            <span>${escapeHtml(run.run_id)}</span>
          </div>
          <span class="status-pill is-${run.status}">${escapeHtml(run.status)}</span>
          <span class="history-meta">${formatTime(run.created_at)}</span>
          <button class="ghost-button" type="button" data-run-id="${escapeHtml(run.run_id)}">查看</button>
        </article>
      `,
    )
    .join("");

  els.historyList.querySelectorAll("[data-run-id]").forEach((button) => {
    button.addEventListener("click", () => selectRun(button.dataset.runId));
  });
}

async function checkHealth() {
  try {
    await requestJson("/api/health");
    setHealth("is-ok", "后端在线");
  } catch (error) {
    setHealth("is-error", "后端离线");
  }
}

async function loadCatalog() {
  const [models, tools] = await Promise.all([requestJson("/api/models"), requestJson("/api/tools")]);
  state.models = models;
  state.tools = tools;
  renderModels();
  renderTools();
}

async function loadRuns() {
  state.runs = await requestJson("/api/runs");
  renderHistory();
}

async function selectRun(runId) {
  closeEventSource();
  const run = await requestJson(`/api/runs/${runId}`);
  renderActiveRun(run);

  if (!terminalStatuses.has(run.status)) {
    openEventStream(run.run_id, run.events.at(-1)?.event_id || 0);
  }
}

function closeEventSource() {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
}

function appendEvent(event) {
  if (!state.activeRun || event.run_id !== state.activeRun.run_id) return;
  const exists = state.activeRun.events.some((item) => item.event_id === event.event_id);
  if (!exists) {
    state.activeRun.events.push(event);
  }
  if (statusFromEvent[event.type]) {
    state.activeRun.status = statusFromEvent[event.type];
  }
  renderActiveRun({ ...state.activeRun });
}

function openEventStream(runId, after = 0) {
  closeEventSource();
  const source = new EventSource(apiUrl(`/api/runs/${runId}/events?after=${after}`));
  state.eventSource = source;

  sseEvents.forEach((eventName) => {
    source.addEventListener(eventName, async (message) => {
      if (eventName === "error" && !message.data) return;
      const event = JSON.parse(message.data);
      appendEvent(event);

      if (terminalStatuses.has(event.type) || eventName === "error") {
        source.close();
        state.eventSource = null;
        const latest = await requestJson(`/api/runs/${runId}`);
        renderActiveRun(latest);
        await loadRuns();
      }
    });
  });

  source.onerror = () => {
    if (!state.activeRun || terminalStatuses.has(state.activeRun.status)) return;
    showToast("事件流连接中断，稍后可手动刷新状态。");
  };
}

function buildPayload() {
  const query = els.queryInput.value.trim();
  if (!query) {
    throw new Error("问题不能为空。");
  }

  const enabledTools = selectedToolNames();
  if (!enabledTools.length) {
    throw new Error("至少选择一个工具。");
  }

  const model = els.modelSelect.value || "dashscope";
  const toolEngine = enabledTools.map((name) => {
    const tool = state.tools.find((item) => item.name === name);
    return tool?.recommended_engine || "self";
  });

  return {
    query,
    llm_engine_name: model,
    enabled_tools: enabledTools,
    tool_engine: toolEngine,
    model_engine: ["trainable", model, model, model],
    output_types: "final,direct",
    max_steps: Number(els.maxStepsInput.value),
    max_time: Number(els.maxTimeInput.value),
    max_tokens: Number(els.maxTokensInput.value),
    temperature: Number(els.temperatureInput.value),
    verbose: els.verboseInput.checked,
    base_url: els.baseUrlInput.value.trim() || null,
  };
}

async function createRun(event) {
  event.preventDefault();
  const payload = buildPayload();
  els.runButton.disabled = true;
  els.runButton.textContent = "提交中";

  try {
    const created = await requestJson("/api/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const run = await requestJson(created.detail_url);
    renderActiveRun(run);
    openEventStream(created.run_id, run.events.at(-1)?.event_id || 0);
    await loadRuns();
    showToast("任务已提交。");
  } catch (error) {
    showToast(error.message);
  } finally {
    els.runButton.disabled = false;
    els.runButton.textContent = "开始推理";
  }
}

function fillExample() {
  els.queryInput.value = "杭州最有名的湖叫什么？请用一句话回答，并说明它为什么有名。";
  els.maxStepsInput.value = "3";
  els.maxTimeInput.value = "180";
  els.temperatureInput.value = "0";
  showToast("已填入一个轻量示例。");
}

function selectBasicTools() {
  els.toolGrid.querySelectorAll("input[type='checkbox']").forEach((input) => {
    input.checked = input.value === "Base_Generator_Tool";
    input.closest(".tool-card").classList.toggle("is-selected", input.checked);
  });
}

async function refreshActiveRun() {
  if (!state.activeRun) {
    await loadRuns();
    showToast("历史任务已更新。");
    return;
  }

  const run = await requestJson(`/api/runs/${state.activeRun.run_id}`);
  renderActiveRun(run);
  await loadRuns();
  showToast("运行状态已刷新。");
}

async function copyResult() {
  const text = els.resultOutput.textContent.trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showToast("结果已复制。");
  } catch {
    showToast("浏览器暂不允许复制，请手动选择内容。");
  }
}

async function init() {
  renderTimeline();
  renderHistory();
  setStatus("idle");

  els.runForm.addEventListener("submit", createRun);
  els.refreshButton.addEventListener("click", refreshActiveRun);
  els.historyRefreshButton.addEventListener("click", loadRuns);
  els.exampleButton.addEventListener("click", fillExample);
  els.selectBasicTools.addEventListener("click", selectBasicTools);
  els.copyResultButton.addEventListener("click", copyResult);

  await checkHealth();
  try {
    await loadCatalog();
    await loadRuns();
  } catch (error) {
    showToast(error.message);
  }
}

init();
