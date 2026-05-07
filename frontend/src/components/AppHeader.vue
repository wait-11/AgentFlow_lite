<script setup>
defineProps({
  health: {
    type: Object,
    required: true,
  },
});
</script>

<template>
  <header class="app-header">
    <div class="brand">
      <img :src="'/assets/img/logo.svg'" alt="AgentFlow" class="brand-logo" />
      <div>
        <p class="eyebrow">AgentFlow Lite</p>
        <h1>推理工作台</h1>
      </div>
    </div>
    <div class="header-actions">
      <span class="health-badge" :class="health.status">
        <span class="status-dot"></span>
        {{ health.label }}
      </span>
      <a href="/docs" class="docs-link">API Docs</a>
    </div>
  </header>
</template>
