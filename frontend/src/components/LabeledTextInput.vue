<script setup lang="ts">
import {computed} from 'vue'

const modelValue = defineModel<string>()

const props = defineProps<{
  title: string
  disabled?: boolean
  password?: boolean
}>()

const type = computed(() => {
  return props.password ? 'password' : 'text'
})
</script>

<template>
  <div class="flex flex-row items-center">
    <label class="mr-2 w-32">{{ title }}</label>
    <input
      :type="type"
      class="border border-slate-600 rounded outline-none py-1 px-2 disabled:text-slate-100 disabled:bg-slate-200 flex-grow"
      v-model="modelValue"
      :disabled="disabled"
    />
  </div>
</template>
