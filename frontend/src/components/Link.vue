<script setup lang="ts">
defineProps<{
  href?: string
  title: string
}>()
</script>

<template>
  <a
    :href="href"
    class="decoration-slate-900 transition-colors underline decoration-1 hover:decoration-2"
  >
    {{ title }}
  </a>
</template>
