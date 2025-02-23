<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <h1 class="font-bold text-2xl pt-8">
    {{ title }}
  </h1>
</template>
