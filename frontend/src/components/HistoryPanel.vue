<script setup>
import { formatTime } from "../utils/formatters";

defineProps({
  runs: {
    type: Array,
    required: true,
  },
});

defineEmits(["refresh-runs", "select-run"]);
</script>

<template>
  <section class="history-panel" aria-labelledby="historyTitle">
    <div class="section-heading">
      <div>
        <p class="eyebrow">History</p>
        <h2 id="historyTitle">最近任务</h2>
      </div>
      <button class="ghost-button" type="button" @click="$emit('refresh-runs')">更新列表</button>
    </div>
    <div class="history-list">
      <div v-if="!runs.length" class="empty-state">还没有任务记录</div>
      <article v-for="run in runs" v-else :key="run.run_id" class="history-row">
        <div class="history-query">
          <strong>{{ run.request.query }}</strong>
          <span>{{ run.run_id }}</span>
        </div>
        <span class="status-pill" :class="`is-${run.status}`">{{ run.status }}</span>
        <span class="history-meta">{{ formatTime(run.created_at) }}</span>
        <button class="ghost-button" type="button" @click="$emit('select-run', run.run_id)">查看</button>
      </article>
    </div>
  </section>
</template>
