<script setup lang="ts">
import {nextTick, ref, watch, watchEffect} from 'vue'

import Button from 'primevue/button'

import {debounce} from '../utilities/utils'

const props = defineProps<{
  id: number
  source: string
  target: string
  focusedId?: number
  editable?: boolean
  disabled?: boolean
  approved?: boolean
  repetitionsCount?: number
}>()

const emit = defineEmits<{
  commit: [string]
  updateRecord: [string]
  focus: []
}>()

const targetInput = ref<HTMLElement | null>(null)

const commitData = debounce(() => {
  if (!targetInput.value?.textContent) {
    return
  }
  emit('updateRecord', targetInput.value.textContent)
}, 1000)

const onKeyPress = (event: KeyboardEvent) => {
  if (!targetInput.value?.textContent) {
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
  async () => {
    // to avoid cursor dropping to 0 position after backend response
    const oldBaseOffset = document.getSelection()?.focusOffset
    if (oldBaseOffset && targetInput.value) {
      await nextTick(() => {
        document
          .getSelection()
          ?.collapse(targetInput.value!.childNodes[0], oldBaseOffset)
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
    <div class="p-2 text-center w-16 relative">
      {{ id }}
      <div
        v-if="editable && repetitionsCount && repetitionsCount > 1"
        class="absolute top-1 right-1 w-2 h-2 bg-orange-500 rounded-full"
        :title="`Repeated ${repetitionsCount} times`"
      />
    </div>
    <div
      class="border rounded-border border-surface p-2 w-1/2 bg-white"
      :class="{'bg-surface-200': disabled ?? false}"
    >
      {{ source }}
    </div>
    <div
      ref="targetInput"
      class="border rounded-border border-surface p-2 bg-white w-1/2"
      :class="{
        'bg-surface-200': disabled ?? false,
        'active:border-primary': editable ?? false,
        'focus:border-primary': editable ?? false,
        'focus:outline-none': editable ?? false,
      }"
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
