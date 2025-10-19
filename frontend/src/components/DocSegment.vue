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
  <i
    class="pi align-middle ml-2 cursor-pointer self-center"
    :class="{
      'pi-arrow-circle-down': repeatEnabled,
      'pi-times-circle text-red-800': !repeatEnabled,
      'opacity-0': !(editable && repetitionsCount && repetitionsCount > 1),
    }"
    :title="repetitionTitle"
    @click="enableRepeat"
  />
  <div class="p-2 text-end relative">
    {{ id }}
  </div>
  <div
    class="border rounded-border border-surface p-2 bg-white h-full"
    :class="{'bg-surface-200': disabled ?? false}"
  >
    {{ source }}
  </div>
  <div
    ref="targetInput"
    class="border rounded-border border-surface p-2 bg-white h-full"
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
    class="text-center w-16 self-start"
  >
    <Button
      icon="pi pi-check"
      size="small"
      :severity="approved ? 'success' : 'primary'"
      :outlined="!approved"
      @click="emit('commit', targetInput?.textContent ?? '', repeatEnabled)"
    />
  </div>
</template>
