<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {MandeError} from 'mande'

import {createXliff, processXliff} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {MachineTranslationSettings} from '../client/schemas/MachineTranslationSettings'

import {useTmxStore} from '../stores/tmx'

import AppButton from './AppButton.vue'
import AppCheckbox from './AppCheckbox.vue'
import LabeledTextInput from './LabeledTextInput.vue'
import TmxFilesModal from './TmxFilesModal.vue'

const emit = defineEmits<{
  uploaded: []
  processed: [fileId: number]
}>()

defineProps<{
  title: string
}>()

const input = ref<HTMLInputElement | null>(null)
const file = ref(null) as Ref<File | null>
const uploadedFile = ref(null) as Ref<XliffFile | null>
const uploading = ref(false)
const status = ref('')
const substituteNumbers = ref(false)
const useMachineTranslation = ref(false)
const machineTranslationSettings = ref<MachineTranslationSettings>({
  folder_id: '',
  oauth_token: '',
})

const processingAvailable = computed(() => uploadedFile.value != null)
const tmxStore = useTmxStore()

const modalOpen = ref(false)
const toggleModal = async () => {
  modalOpen.value = !modalOpen.value
}

const createFile = async () => {
  status.value = ''
  const inputElement = input.value
  if (!inputElement?.files) {
    return
  }

  file.value = inputElement.files[0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    uploadedFile.value = await createXliff({file: file.value})
    uploading.value = false
    status.value = 'Ready for processing'
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

const startProcessing = async () => {
  if (!processingAvailable.value) {
    return
  }

  status.value = ''

  try {
    uploading.value = true
    status.value = 'Processing...'
    await processXliff(uploadedFile.value!.id, {
      substitute_numbers: substituteNumbers.value,
      use_machine_translation: useMachineTranslation.value,
      machine_translation_settings: useMachineTranslation.value
        ? machineTranslationSettings.value
        : null,
      tmx_file_ids: tmxStore.selectedIds,
    })
    uploading.value = false
    status.value = 'Done!'
    emit('processed', uploadedFile.value!.id)
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}
</script>

<template>
  <div class="border border-slate-500 p-2 min-w-96">
    <div>
      <label
        for="file"
        class="font-semibold mr-2"
      >
        {{ title }}
      </label>
      <input
        id="file-input"
        ref="input"
        type="file"
        accept=".xliff"
        :disabled="uploading"
        @change="createFile"
      />
      <span
        v-if="status"
        class="ml-2"
      >
        {{ status }}
      </span>
    </div>

    <div
      v-if="processingAvailable"
      class="mt-3"
    >
      <p class="font-semibold">Processing options</p>
      <p class="mt-2">
        Selected TMX files: {{ tmxStore.selectedCount }} /
        {{ tmxStore.totalCount }}
      </p>
      <AppButton @click="toggleModal">Select TMX files to use</AppButton>
      <AppCheckbox
        v-model:value="substituteNumbers"
        class="mt-2"
        title="Substitute segments with numbers only"
      />
      <AppCheckbox
        v-model:value="useMachineTranslation"
        title="Use Yandex machine translation"
      />
      <div v-if="useMachineTranslation">
        <p class="font-semibold mt-3 mb-1">
          Yandex translator options
          <a
            href="https://yandex.cloud/ru/docs/translate/api-ref/authentication"
            class="font-normal underline decoration-1 hover:decoration-2"
            target="_blank"
          >
            (Where to get credentials?)
          </a>
        </p>
        <LabeledTextInput
          class="mb-2"
          v-model="machineTranslationSettings.folder_id"
          title="Folder ID"
        />
        <LabeledTextInput
          v-model="machineTranslationSettings.oauth_token"
          title="OAuth token"
        />
      </div>
    </div>

    <div
      v-if="processingAvailable"
      class="mt-5"
    >
      <AppButton
        :disabled="!processingAvailable || uploading"
        @click="startProcessing"
      >
        Start processing
      </AppButton>
    </div>
  </div>

  <TmxFilesModal
    :open="modalOpen"
    @close="toggleModal"
  />
</template>
