<script setup lang="ts">
import {computed, nextTick, ref, watch, watchEffect} from 'vue'

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
  commit: [string, boolean]
  updateRecord: [string, boolean]
  focus: []
}>()

const targetInput = ref<HTMLElement | null>(null)

const commitData = debounce(() => {
  if (!targetInput.value?.textContent) {
    return
  }
  emit('updateRecord', targetInput.value.textContent, repeatEnabled.value)
}, 1000)

const onKeyPress = (event: KeyboardEvent) => {
  if (!targetInput.value?.textContent) {
    return
  }
  if (event.key == 'Enter' && event.ctrlKey) {
    emit('commit', targetInput.value.textContent, repeatEnabled.value)
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

const repeatEnabled = ref(true)
const enableRepeat = () => {
  repeatEnabled.value = !repeatEnabled.value
}
const repetitionTitle = computed(() => {
  return (
    'Click to ' +
    (repeatEnabled.value ? 'disable' : 'enable') +
    ` updating of the same segments. Repeated ${props.repetitionsCount} times.`
  )
})
</script>

<template>
  <div class="flex flex-row gap-2 font-text">
    <div class="p-2 text-end w-28 relative">
      <i
        v-if="editable && repetitionsCount && repetitionsCount > 1"
        class="pi align-middle mr-1 cursor-pointer"
        :class="{
          'pi-arrow-circle-down': repeatEnabled,
          'pi-times-circle text-red-800': !repeatEnabled,
        }"
        :title="repetitionTitle"
        @click="enableRepeat"
      />
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
        @click="emit('commit', targetInput?.textContent ?? '', repeatEnabled)"
      />
    </div>
  </div>
</template>
