<script setup lang="ts">
const modelValue = defineModel<string>()
defineProps<{
  title: string
  disabled?: boolean
}>()
</script>

<template>
  <div class="flex flex-row items-center">
    <label class="mr-2 w-32">{{ title }}</label>
    <input
      type="text"
      class="border border-slate-600 rounded outline-none py-1 px-2 disabled:text-slate-100 disabled:bg-slate-200"
      v-model="modelValue"
      :disabled="disabled"
    />
  </div>
</template>
