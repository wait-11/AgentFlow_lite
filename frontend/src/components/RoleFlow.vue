<script setup>
import { formatTime } from "../utils/formatters";

defineProps({
  activityCount: {
    type: Number,
    required: true,
  },
  roles: {
    type: Array,
    required: true,
  },
});
</script>

<template>
  <div class="role-visualization" aria-labelledby="roleFlowTitle">
    <div class="label-row">
      <div>
        <span id="roleFlowTitle">角色分工</span>
        <p class="role-caption">Planner 规划，Executor 调工具，Memory 记录上下文，Verifier 决定继续或停止。</p>
      </div>
      <span class="muted">{{ activityCount }} role events</span>
    </div>
    <div class="role-flow">
      <article
        v-for="role in roles"
        :key="role.key"
        class="role-card"
        :class="[`role-${role.key}`, { 'is-active': role.active }]"
      >
        <div class="role-head">
          <div>
            <h3 class="role-title">{{ role.title }}</h3>
            <span class="role-subtitle">{{ role.subtitle }} · {{ role.engine }}</span>
          </div>
          <span class="role-count">{{ role.count }}</span>
        </div>
        <p class="role-duties">{{ role.duties }}</p>
        <div class="role-latest">
          <span>{{ role.latest ? `${role.latest.type} · ${formatTime(role.latest.timestamp)}` : "latest activity" }}</span>
          <strong>{{ role.latestSummary }}</strong>
        </div>
      </article>
    </div>
  </div>
</template>
