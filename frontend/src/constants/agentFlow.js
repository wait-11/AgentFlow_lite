export const terminalStatuses = new Set(["completed", "failed", "cancelled"]);

export const sseEvents = [
  "queued",
  "started",
  "solver_constructing",
  "solver_ready",
  "query_received",
  "base_response",
  "query_analysis",
  "planner_action",
  "tool_unavailable",
  "executor_command",
  "tool_result",
  "memory_update",
  "verifier_result",
  "final_output",
  "direct_output",
  "completed",
  "failed",
  "error",
];

export const statusFromEvent = {
  queued: "queued",
  started: "running",
  solver_constructing: "running",
  solver_ready: "running",
  completed: "completed",
  failed: "failed",
};

export const roleDefinitions = [
  {
    key: "planner",
    title: "Planner",
    subtitle: "规划与总结",
    duties: "分析问题，拆解下一步目标，选择工具，并在结束时组织最终答案。",
    eventTypes: ["base_response", "query_analysis", "planner_action", "final_output", "direct_output"],
  },
  {
    key: "executor",
    title: "Executor",
    subtitle: "命令与工具",
    duties: "把 Planner 的目标转成工具命令，执行工具调用，并返回可用结果。",
    eventTypes: ["tool_unavailable", "executor_command", "tool_result"],
  },
  {
    key: "memory",
    title: "Memory",
    subtitle: "上下文记录",
    duties: "沉淀每一步的目标、命令和结果，为后续推理提供共享上下文。",
    eventTypes: ["memory_update"],
  },
  {
    key: "verifier",
    title: "Verifier",
    subtitle: "质量检查",
    duties: "检查当前上下文是否足够回答问题，决定继续推理或停止输出。",
    eventTypes: ["verifier_result"],
  },
];
