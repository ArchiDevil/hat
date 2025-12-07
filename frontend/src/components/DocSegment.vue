<script setup lang="ts">
import {computed, ref, useTemplateRef, watch} from 'vue'

import Button from 'primevue/button'

import {cleanableDebounce} from '../utilities/utils'
import {RecordSource} from '../client/schemas/RecordSource'

const props = defineProps<{
  id: number
  source: string
  target: string
  focused?: boolean
  editable?: boolean
  disabled?: boolean
  approved?: boolean
  repetitionsCount?: number
  hasComments?: boolean
  recordSrc?: RecordSource
}>()

const emit = defineEmits<{
  commit: [string, boolean]
  updateRecord: [string, boolean]
  focus: []
  startEdit: []
  addComment: []
}>()

const targetInput = useTemplateRef('targetInput')

const {func: updateData, clear: clearUpdate} = cleanableDebounce(() => {
  if (!targetInput.value?.textContent) return
  emit('updateRecord', targetInput.value.textContent, repeatEnabled.value)
}, 1000)

const commitData = () => {
  clearUpdate()
  emit('commit', targetInput.value?.textContent ?? '', repeatEnabled.value)
}

const onKeyPress = (event: KeyboardEvent) => {
  if (!targetInput.value?.textContent) {
    return
  }
  if (event.key == 'Enter' && event.ctrlKey) {
    commitData()
  }
}

watch(
  () => props.focused,
  () => {
    if (props.focused) {
      targetInput.value?.focus()
    }
  }
)

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

const icon = computed(
  () => 'pi' + (props.hasComments ? ' pi-comments' : ' pi-comment')
)

const showCommentsDialog = () => {
  emit('addComment')
}

const segSourceTitle = computed(() => {
  switch (props.recordSrc) {
    case 'glossary':
      return 'Glossary term'
    case 'mt':
      return 'Machine translation'
    case 'tm':
      return 'Translation memory'
    default:
      return undefined
  }
})

const segSourceIcon = computed(() => {
  switch (props.recordSrc) {
    case 'glossary':
      return 'pi-globe'
    case 'mt':
      return 'pi-language'
    case 'tm':
      return 'pi-database'
    default:
      return undefined
  }
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
    class="border rounded-border border-surface p-2 bg-white h-full h-min-11"
    :class="{'bg-surface-200': disabled ?? false}"
  >
    {{ source }}
  </div>
  <div
    ref="targetInput"
    class="border rounded-border border-surface p-2 bg-white h-full h-min-11"
    :class="{
      'bg-surface-200': disabled ?? false,
      'active:border-primary focus:border-primary focus:outline-none':
        editable ?? false,
    }"
    :contenteditable="editable"
    @input="
      () => {
        emit('startEdit')
        updateData()
      }
    "
    @keypress="onKeyPress"
    @focus="emit('focus')"
  >
    {{ target }}
  </div>
  <div
    v-if="editable"
    class="flex flex-row text-center self-start gap-2 pr-2 h-full"
  >
    <div
      v-if="recordSrc && recordSrc !== 'user'"
      class="py-1 px-2"
      :title="segSourceTitle"
    >
      <i
        class="pi text-surface-500"
        :class="segSourceIcon"
      />
    </div>
    <Button
      class="ml-auto"
      :icon="icon"
      rounded
      outlined
      variant="text"
      :severity="hasComments ? 'help' : 'secondary'"
      size="small"
      @click="showCommentsDialog"
    />
    <Button
      icon="pi pi-check"
      rounded
      :severity="approved ? 'success' : 'secondary'"
      size="small"
      @click="commitData"
    />
  </div>
</template>
