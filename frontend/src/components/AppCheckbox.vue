<script setup lang="ts">
defineProps<{
  title: string
}>()

const value = defineModel<boolean>('value')
</script>

<template>
  <div class="flex flex-row select-none">
    <input
      v-model="value"
      type="checkbox"
    />
    <label
      class="ml-2"
      @click="value = !value"
    >
      {{ title }}
    </label>
  </div>
</template>
