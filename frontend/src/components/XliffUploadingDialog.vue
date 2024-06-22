<script setup lang="ts">
import {Ref, ref, computed, onMounted} from 'vue'
import {MandeError} from 'mande'

import {createXliff, processXliff} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {MachineTranslationSettings} from '../client/schemas/MachineTranslationSettings'

import {useTmxStore} from '../stores/tmx'

import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Select from 'primevue/select'
import FileUpload, {FileUploadSelectEvent} from 'primevue/fileupload'

const emit = defineEmits<{
  uploaded: []
  processed: [fileId: number]
}>()

defineProps<{
  title: string
}>()

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

const createFile = async (event: FileUploadSelectEvent) => {
  status.value = ''
  if (!event.files) {
    return
  }

  const selectedFile = event.files[0] as File

  try {
    uploading.value = true
    status.value = 'Uploading...'
    uploadedFile.value = await createXliff({file: selectedFile})
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
      tmx_usage: tmxStore.tmxMode,
    })
    uploading.value = false
    status.value = 'Done!'
    emit('processed', uploadedFile.value!.id)
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

onMounted(async () => {
  await tmxStore.getTmx()
})
</script>

<template>
  <div class="min-w-96">
    <FileUpload
      mode="advanced"
      custom-upload
      accept=".xliff"
      :disabled="uploading"
      @select="(event: FileUploadSelectEvent) => createFile(event)"
      @uploader="startProcessing"
    >
      <template #content="{files}">
        <div v-if="files.length != 0">
          <p class="font-semibold">Processing options</p>
          <div class="flex flex-col gap-2 mb-4 max-w-96 mt-2">
            <label>TMX files to use:</label>
            <MultiSelect
              class="w-96"
              v-model="tmxStore.selectedTmxFiles"
              placeholder="Select TMX files to use"
              :options="tmxStore.tmxFiles"
              optionLabel="name"
              :filter="false"
              filterPlaceholder="Search TMX files..."
            />
          </div>
          <div class="flex flex-col gap-2 mb-4 max-w-96 mt-2">
            <label>When segment is found in multiple TMXs:</label>
            <Select
              v-model="tmxStore.tmxMode"
              :options="[
                {name: 'Use newest TM', value: 'newest'},
                {name: 'Use oldest TM', value: 'oldest'},
              ]"
              option-label="name"
              option-value="value"
            />
          </div>
          <div class="flex items-center mt-2">
            <Checkbox
              id="sn"
              v-model="substituteNumbers"
              :binary="true"
            />
            <label
              for="sn"
              class="ml-2"
              @click="substituteNumbers = !substituteNumbers"
            >
              Substitute segments with numbers only
            </label>
          </div>
          <div class="flex items-center">
            <Checkbox
              id="umt"
              v-model="useMachineTranslation"
              :binary="true"
            />
            <label
              for="umt"
              class="ml-2"
              @click="useMachineTranslation = !useMachineTranslation"
            >
              Use Yandex machine translation
            </label>
          </div>
          <div
            v-if="useMachineTranslation"
            class="flex flex-col gap-2 max-w-[32rem]"
          >
            <p class="font-semibold mt-3">
              Yandex translator options
              <a
                href="https://yandex.cloud/ru/docs/translate/api-ref/authentication"
                class="font-normal underline decoration-1 hover:decoration-2"
                target="_blank"
              >
                (Where to get credentials?)
              </a>
            </p>
            <div class="flex items-center flex-row gap-2">
              <label
                for="fid"
                class="flex-grow"
              >
                Folder ID
              </label>
              <InputText
                id="fid"
                class="w-96"
                v-model="machineTranslationSettings.folder_id"
              />
            </div>
            <div class="flex items-center flex-row gap-2">
              <label
                for="oauth"
                class="flex-grow"
              >
                OAuth token
              </label>
              <InputText
                id="oauth"
                class="w-96"
                v-model="machineTranslationSettings.oauth_token"
              />
            </div>
          </div>
        </div>
        <div v-else>{{ status }}</div>
      </template>
      <template #empty
        ><span v-if="!status">
          Choose or drag and drop XLIFF file to upload
        </span>
      </template>
    </FileUpload>
  </div>
</template>
