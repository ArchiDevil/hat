<script setup lang="ts">
import {ref, watchEffect} from 'vue'

import {TmxFileRecord} from '../client/schemas/TmxFileRecord'
import {XliffFileRecord} from '../client/schemas/XliffFileRecord'

import {debounce} from '../utils'

const props = defineProps<{
  record: TmxFileRecord | XliffFileRecord
  focusedId?: number
  editable?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  commit: [string]
  updateRecord: [string]
  focus: []
}>()

const targetInput = ref<HTMLElement | null>(null)

const commitData = debounce(async () => {
  if (!targetInput.value || !targetInput.value.textContent) {
    return
  }
  emit('updateRecord', targetInput.value.textContent)
}, 1000)

const onKeyPress = (event: KeyboardEvent) => {
  if (!targetInput.value || !targetInput.value.textContent) {
    return
  }
  if (event.key == 'Enter' && event.ctrlKey) {
    emit('commit', targetInput.value.textContent)
  }
}

const onInput = () => {
  commitData()
}

watchEffect(() => {
  if (props.focusedId == props.record.id) {
    targetInput.value?.focus()
  }
})
</script>

<template>
  <div class="grid grid-cols-11 gap-2">
    <div class="p-2 col-span-1 text-center">
      {{ record.id }}
    </div>
    <div
      class="border rounded-border border-surface p-2 disabled:bg-surface-200 col-span-5"
      :class="{'bg-surface-200': disabled ?? false}"
    >
      {{ record.source }}
    </div>
    <div
      ref="targetInput"
      class="border rounded-border border-surface p-2 active:border-primary focus:border-primary focus:outline-none col-span-5"
      :class="{'bg-surface-200': disabled ?? false}"
      :contenteditable="editable"
      @input="onInput"
      @keypress="onKeyPress"
      @focus="emit('focus')"
    >
      {{ record.target }}
    </div>
  </div>
</template>