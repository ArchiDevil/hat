<script setup lang="ts">
import {nextTick, ref, watch, watchEffect} from 'vue'

import Button from 'primevue/button'

import {debounce} from '../utils'

const props = defineProps<{
  id: number
  source: string
  target: string
  focusedId?: number
  editable?: boolean
  disabled?: boolean
  approved?: boolean
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
}, 5000)

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

watch(
  () => props.target,
  () => {
    // to avoid cursor dropping to 0 position after backend response
    const oldBaseOffset = document.getSelection()?.focusOffset
    if (oldBaseOffset && targetInput.value) {
      nextTick(() => {
        document
          .getSelection()
          ?.collapse(targetInput.value!.childNodes[0]!, oldBaseOffset)
      })
    }
  }
)

watchEffect(() => {
  if (props.focusedId == props.id) {
    targetInput.value?.focus()
  }
})
</script>

<template>
  <div class="flex flex-row gap-2 font-text">
    <div class="p-2 text-center w-16">
      {{ id }}
    </div>
    <div
      class="border rounded-border border-surface p-2 w-1/2 bg-white"
      :class="{'bg-surface-200': disabled ?? false}"
    >
      {{ source }}
    </div>
    <div
      ref="targetInput"
      class="border rounded-border border-surface p-2 bg-white active:border-primary focus:border-primary focus:outline-none w-1/2"
      :class="{'bg-surface-200': disabled ?? false}"
      :contenteditable="editable"
      @input="onInput"
      @keypress="onKeyPress"
      @focus="emit('focus')"
    >
      {{ target }}
    </div>
    <div
      v-if="editable"
      class="mr-2 text-center w-16 py-1"
    >
      <Button
        icon="pi pi-check"
        size="small"
        :severity="approved ? 'success' : 'primary'"
        :outlined="!approved"
        @click="emit('commit', targetInput?.textContent ?? '')"
      />
    </div>
  </div>
</template>
