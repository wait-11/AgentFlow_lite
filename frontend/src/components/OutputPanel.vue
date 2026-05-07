<script setup>
import ResultBox from "./ResultBox.vue";
import RoleFlow from "./RoleFlow.vue";
import TimelineList from "./TimelineList.vue";

defineProps({
  activeRun: {
    type: Object,
    default: null,
  },
  activeStatus: {
    type: String,
    required: true,
  },
  eventCount: {
    type: Number,
    required: true,
  },
  resultOutput: {
    type: String,
    required: true,
  },
  roleActivityCount: {
    type: Number,
    required: true,
  },
  roleCards: {
    type: Array,
    required: true,
  },
});

defineEmits(["copy-result", "refresh-active-run"]);
</script>

<template>
  <section class="output-panel" aria-labelledby="currentRunTitle">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Current Run</p>
        <h2 id="currentRunTitle">运行状态</h2>
      </div>
      <button class="ghost-button" type="button" @click="$emit('refresh-active-run')">刷新</button>
    </div>

    <div class="run-summary">
      <div>
        <span class="summary-label">Run ID</span>
        <strong>{{ activeRun?.run_id || "尚未创建" }}</strong>
      </div>
      <span class="status-pill" :class="`is-${activeStatus}`">{{ activeStatus }}</span>
    </div>

    <RoleFlow :activity-count="roleActivityCount" :roles="roleCards" />
    <ResultBox :output="resultOutput" @copy-result="$emit('copy-result')" />
    <TimelineList :event-count="eventCount" :events="activeRun?.events || []" />
  </section>
</template>
