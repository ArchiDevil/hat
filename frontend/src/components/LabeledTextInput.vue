<script setup lang="ts">
const modelValue = defineModel<string>()
defineProps<{
  title: string
}>()
</script>

<template>
  <div class="flex flex-row items-center">
    <label class="mr-2">{{ title }}</label>
    <input
      type="text"
      class="border border-slate-600 rounded outline-none py-1 px-2"
      v-model="modelValue"
    >
  </div>
</template>

<style scoped></style>
