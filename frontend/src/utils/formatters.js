import { roleDefinitions } from "../constants/agentFlow";

export function formatTime(value) {
  if (!value) return "--";
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function summarizeOutput(run) {
  if (!run) return "提交任务后，结果会显示在这里。";
  if (run.error) return run.error;
  if (!run.output) return "任务正在运行，等待最终输出。";
  return run.output.direct_output || run.output.final_output || JSON.stringify(run.output, null, 2);
}

export function compactText(value, maxLength = 92) {
  let text = "";
  if (typeof value === "string") {
    text = value;
  } else if (value !== undefined && value !== null) {
    text = JSON.stringify(value);
  }
  text = text.replace(/\s+/g, " ").trim();
  if (!text) return "等待角色开始工作";
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

export function buildRoleCards(run) {
  const events = run?.events || [];
  const roleEventTypes = new Set(roleDefinitions.flatMap((role) => role.eventTypes));
  const roleEvents = events.filter((event) => roleEventTypes.has(event.type));
  const latestRoleKey = roleDefinitions.find((role) => role.eventTypes.includes(roleEvents.at(-1)?.type))?.key;

  return roleDefinitions.map((role) => {
    const matchingEvents = events.filter((event) => role.eventTypes.includes(event.type));
    const latest = matchingEvents.at(-1);
    return {
      ...role,
      count: matchingEvents.length,
      engine: roleEngineLabel(role, run),
      latest,
      latestSummary: summarizeRoleEvent(latest),
      active: role.key === latestRoleKey,
    };
  });
}

function resolveEngineName(engine, run) {
  if (!engine || engine === "trainable") return run?.request?.llm_engine_name || "主模型";
  return engine;
}

function roleEngineLabel(role, run) {
  const modelEngine = run?.request?.model_engine || [];
  if (role.key === "planner") {
    const main = resolveEngineName(modelEngine[0], run);
    const fixed = resolveEngineName(modelEngine[1], run);
    return main === fixed ? main : `${main} / fixed ${fixed}`;
  }
  if (role.key === "executor") return resolveEngineName(modelEngine[3], run);
  if (role.key === "verifier") return resolveEngineName(modelEngine[2], run);
  return "本地运行时";
}

function summarizeRoleEvent(event) {
  if (!event) return "等待角色开始工作";
  const data = event.data || {};
  switch (event.type) {
    case "query_analysis":
      return compactText(data.analysis);
    case "planner_action":
      return compactText(data.sub_goal || data.context || data.tool_name);
    case "executor_command":
      return compactText(data.explanation || data.command || data.tool_name);
    case "tool_result":
      return compactText(data.result || data.command || data.tool_name);
    case "memory_update":
      return compactText(data.sub_goal || data.memory || "已记录当前 step 的动作与结果");
    case "verifier_result":
      return compactText(`${data.conclusion || "VERIFY"} ${data.analysis || ""}`);
    case "final_output":
    case "direct_output":
      return compactText(data.output);
    case "tool_unavailable":
      return compactText(`工具不可用：${data.tool_name || "unknown"}`);
    default:
      return compactText(event.message);
  }
}
