<script setup lang="ts">
defineProps<{open: boolean}>()
</script>

<template>
  <Teleport to="#modal">
    <div
      v-if="open"
      class="fixed top-0 left-0 z-40 bg-slate-500/60 w-dvw h-dvh rounded-border"
    />
    <div
      v-if="open"
      class="border border-surface bg-slate-50 fixed z-50 top-20 left-1/2 w-96 -ml-48 rounded-border"
    >
      <slot />
    </div>
  </Teleport>
</template>
