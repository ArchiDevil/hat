<script setup lang="ts">
defineEmits<{
  click: [Event]
}>()
</script>

<template>
  <button @click="($event) => $emit('click', $event)">
    <slot></slot>
  </button>
</template>

<style scoped>
button {
  @apply py-1 px-2 h-8;
  @apply border rounded border-slate-600;
  @apply bg-slate-400;
  @apply transition-colors;
}

button:hover {
  @apply bg-slate-600 text-slate-50;
}

button:disabled {
  @apply border-slate-300 bg-slate-200 text-slate-50;
}
</style>
