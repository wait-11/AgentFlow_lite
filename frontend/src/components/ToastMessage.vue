<script setup>
defineProps({
  message: {
    type: String,
    default: "",
  },
  visible: {
    type: Boolean,
    required: true,
  },
});
</script>

<template>
  <div class="toast" :class="{ 'is-visible': visible }" role="status" aria-live="polite">
    {{ message }}
  </div>
</template>
