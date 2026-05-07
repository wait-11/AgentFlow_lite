import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { sseEvents, statusFromEvent, terminalStatuses } from "../constants/agentFlow";
import { apiUrl, requestJson } from "../services/api";
import { buildRoleCards, summarizeOutput } from "../utils/formatters";

export function useWorkbench() {
  const tools = ref([]);
  const models = ref([]);
  const runs = ref([]);
  const activeRun = ref(null);
  const eventSource = ref(null);
  const toastMessage = ref("");
  const toastVisible = ref(false);
  const isSubmitting = ref(false);
  let toastTimer;

  const health = reactive({
    status: "",
    label: "正在连接",
  });

  const form = reactive({
    query: "",
    model: "dashscope",
    baseUrl: "",
    selectedTools: new Set(),
    maxSteps: 6,
    maxTime: 300,
    maxTokens: 4000,
    temperature: 0,
    verbose: false,
  });

  const activeStatus = computed(() => activeRun.value?.status || "idle");
  const resultOutput = computed(() => summarizeOutput(activeRun.value));
  const sortedRuns = computed(() =>
    [...runs.value].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
  );
  const eventCount = computed(() => activeRun.value?.events?.length || 0);
  const roleCards = computed(() => buildRoleCards(activeRun.value));
  const roleActivityCount = computed(() => roleCards.value.reduce((sum, role) => sum + role.count, 0));

  function showToast(message) {
    toastMessage.value = message;
    toastVisible.value = true;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastVisible.value = false;
    }, 2600);
  }

  function toggleTool(toolName) {
    if (form.selectedTools.has(toolName)) {
      form.selectedTools.delete(toolName);
    } else {
      form.selectedTools.add(toolName);
    }
  }

  function selectBasicTools() {
    form.selectedTools = new Set(["Base_Generator_Tool"]);
  }

  function buildPayload() {
    const query = form.query.trim();
    if (!query) throw new Error("问题不能为空。");

    const enabledTools = [...form.selectedTools];
    if (!enabledTools.length) throw new Error("至少选择一个工具。");

    const toolEngine = enabledTools.map((name) => {
      const tool = tools.value.find((item) => item.name === name);
      return tool?.recommended_engine || "self";
    });

    return {
      query,
      llm_engine_name: form.model || "dashscope",
      enabled_tools: enabledTools,
      tool_engine: toolEngine,
      model_engine: ["trainable", form.model || "dashscope", form.model || "dashscope", form.model || "dashscope"],
      output_types: "final,direct",
      max_steps: Number(form.maxSteps),
      max_time: Number(form.maxTime),
      max_tokens: Number(form.maxTokens),
      temperature: Number(form.temperature),
      verbose: form.verbose,
      base_url: form.baseUrl.trim() || null,
    };
  }

  function closeEventSource() {
    if (eventSource.value) {
      eventSource.value.close();
      eventSource.value = null;
    }
  }

  function appendEvent(event) {
    if (!activeRun.value || event.run_id !== activeRun.value.run_id) return;
    const exists = activeRun.value.events.some((item) => item.event_id === event.event_id);
    if (!exists) activeRun.value.events.push(event);
    if (statusFromEvent[event.type]) activeRun.value.status = statusFromEvent[event.type];
  }

  function openEventStream(runId, after = 0) {
    closeEventSource();
    const source = new EventSource(apiUrl(`/api/runs/${runId}/events?after=${after}`));
    eventSource.value = source;

    sseEvents.forEach((eventName) => {
      source.addEventListener(eventName, async (message) => {
        if (eventName === "error" && !message.data) return;
        const event = JSON.parse(message.data);
        appendEvent(event);

        if (terminalStatuses.has(event.type) || eventName === "error") {
          source.close();
          eventSource.value = null;
          const latest = await requestJson(`/api/runs/${runId}`);
          activeRun.value = latest;
          await loadRuns();
        }
      });
    });

    source.onerror = () => {
      if (!activeRun.value || terminalStatuses.has(activeRun.value.status)) return;
      showToast("事件流连接中断，稍后可手动刷新状态。");
    };
  }

  async function checkHealth() {
    try {
      await requestJson("/api/health");
      health.status = "is-ok";
      health.label = "后端在线";
    } catch {
      health.status = "is-error";
      health.label = "后端离线";
    }
  }

  async function loadCatalog() {
    const [loadedModels, loadedTools] = await Promise.all([requestJson("/api/models"), requestJson("/api/tools")]);
    models.value = loadedModels;
    tools.value = loadedTools;
    form.model = loadedModels[0]?.name || "dashscope";
    form.selectedTools = new Set(loadedTools[0] ? [loadedTools[0].name] : []);
  }

  async function loadRuns() {
    runs.value = await requestJson("/api/runs");
  }

  async function selectRun(runId) {
    closeEventSource();
    const run = await requestJson(`/api/runs/${runId}`);
    activeRun.value = run;
    if (!terminalStatuses.has(run.status)) {
      openEventStream(run.run_id, run.events.at(-1)?.event_id || 0);
    }
  }

  async function createRun() {
    let payload;
    try {
      payload = buildPayload();
    } catch (error) {
      showToast(error.message);
      return;
    }

    isSubmitting.value = true;
    try {
      const created = await requestJson("/api/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      activeRun.value = await requestJson(created.detail_url);
      openEventStream(created.run_id, activeRun.value.events.at(-1)?.event_id || 0);
      await loadRuns();
      showToast("任务已提交。");
    } catch (error) {
      showToast(error.message);
    } finally {
      isSubmitting.value = false;
    }
  }

  function fillExample() {
    form.query = "杭州最有名的湖叫什么？请用一句话回答，并说明它为什么有名。";
    form.maxSteps = 3;
    form.maxTime = 180;
    form.temperature = 0;
    showToast("已填入一个轻量示例。");
  }

  async function refreshActiveRun() {
    if (!activeRun.value) {
      await loadRuns();
      showToast("历史任务已更新。");
      return;
    }

    activeRun.value = await requestJson(`/api/runs/${activeRun.value.run_id}`);
    await loadRuns();
    showToast("运行状态已刷新。");
  }

  async function copyResult() {
    const text = resultOutput.value.trim();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      showToast("结果已复制。");
    } catch {
      showToast("浏览器暂不允许复制，请手动选择内容。");
    }
  }

  onMounted(async () => {
    await checkHealth();
    try {
      await loadCatalog();
      await loadRuns();
    } catch (error) {
      showToast(error.message);
    }
  });

  onBeforeUnmount(() => {
    closeEventSource();
    window.clearTimeout(toastTimer);
  });

  return {
    activeRun,
    activeStatus,
    copyResult,
    createRun,
    eventCount,
    fillExample,
    form,
    health,
    isSubmitting,
    loadRuns,
    models,
    refreshActiveRun,
    resultOutput,
    roleActivityCount,
    roleCards,
    selectBasicTools,
    selectRun,
    sortedRuns,
    toastMessage,
    toastVisible,
    toggleTool,
    tools,
  };
}
