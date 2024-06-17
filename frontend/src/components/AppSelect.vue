<script setup lang="ts">
defineProps<{
  title: string
  options: {name: string; value: string}[]
}>()
</script>

<template>
  <div>
    <label class="min-w-32 inline-block mr-2">{{ title }}</label>
    <select>
      <option
        v-for="opt in options"
        :value="opt.value"
      >
        {{ opt.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
select {
  @apply max-w-32 px-2 py-1 border rounded bg-slate-300 transition-colors;
  @apply hover:cursor-pointer hover:bg-slate-500 hover:text-slate-50;
}
</style>
