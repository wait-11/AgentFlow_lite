<script setup>
defineProps({
  output: {
    type: String,
    required: true,
  },
});

defineEmits(["copy-result"]);
</script>

<template>
  <div class="result-box">
    <div class="result-header">
      <span>最终答案</span>
      <button class="link-button" type="button" @click="$emit('copy-result')">复制</button>
    </div>
    <pre>{{ output }}</pre>
  </div>
</template>
