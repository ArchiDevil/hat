<script setup lang="ts">
defineProps<{
  title: string
  disabled?: boolean
}>()

const value = defineModel<boolean>('value')
</script>

<template>
  <div class="flex flex-row select-none">
    <input
      v-model="value"
      type="checkbox"
      :disabled="disabled"
    />
    <label
      class="ml-2 text-slate-900"
      @click="value = !value"
    >
      {{ title }}
    </label>
  </div>
</template>
