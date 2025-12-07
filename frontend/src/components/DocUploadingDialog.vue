<script setup lang="ts">
import {Ref, ref, computed, onMounted} from 'vue'
import {MandeError} from 'mande'

import {
  createDoc,
  processDoc,
  setGlossaries,
  setTranslationMemories,
} from '../client/services/DocumentService'
import {Document} from '../client/schemas/Document'

import {useTmStore} from '../stores/tm'
import {useGlossaryStore} from '../stores/glossary'

import MachineTranslationOptions, {
  MtType,
} from './MachineTranslationOptions.vue'

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

const uploadedFile = ref(null) as Ref<Document | null>
const uploading = ref(false)
const status = ref('')

const mtOptions = ref({
  enabled: false,
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  type: 'yandex' as MtType,
  yandexSettings: {
    type: 'yandex',
    folder_id: '',
    oauth_token: '',
  },
  llmSettings: {
    type: 'llm',
    api_key: '',
  },
})
const similarityThreshold = ref<number>(1.0)

const processingAvailable = computed(() => uploadedFile.value != null)
const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const createFile = async (event: FileUploadSelectEvent) => {
  status.value = ''
  if (!event.files) {
    return
  }

  const selectedFile = (event.files as File[])[0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    uploadedFile.value = await createDoc({file: selectedFile})
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
    await setTranslationMemories(uploadedFile.value!.id, {
      memories: selectedTms.value.map((tm) => {
        return {id: tm.id, mode: 'read'}
      }),
    })
    await setGlossaries(uploadedFile.value!.id, {
      glossaries: selectedGlossaries.value.map((g) => {
        return {id: g.id}
      }),
    })
    const mtSettings = mtOptions.value
    await processDoc(uploadedFile.value!.id, {
      machine_translation_settings: mtSettings.enabled
        ? mtSettings.type === 'yandex'
          ? mtSettings.yandexSettings
          : mtSettings.llmSettings
        : null,
      similarity_threshold: similarityThreshold.value,
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
  await tmStore.fetchMemories()
  selectedTms.value = tmStore.memories

  await glossaryStore.fetchGlossaries()
  selectedGlossaries.value = glossaryStore.glossaries
})

const selectedTms = ref<typeof tmStore.memories>([])
const selectedGlossaries = ref<typeof glossaryStore.glossaries>([])
</script>

<template>
  <div class="min-w-96">
    <FileUpload
      mode="advanced"
      custom-upload
      accept=".xliff,.txt"
      :disabled="uploading"
      @select="createFile"
      @uploader="startProcessing"
    >
      <template #content="{files}">
        <div v-if="files.length != 0">
          <p class="font-semibold">
            Processing options
          </p>
          <div class="flex flex-col gap-2 mb-4 max-w-96 mt-2">
            <label>TMX files to use:</label>
            <MultiSelect
              v-model="selectedTms"
              class="w-96"
              placeholder="Select TMX files to use"
              :options="tmStore.memories"
              option-label="name"
              filter
              filter-placeholder="Search TMX files..."
            />
          </div>
          <div class="flex flex-col gap-2 mb-4 max-w-96">
            <label>Substitution similary threshold:</label>
            <Select
              v-model="similarityThreshold"
              :options="[
                {name: '100%', value: 1.0},
                {name: '95%', value: 0.95},
                {name: '90%', value: 0.9},
                {name: '85%', value: 0.85},
                {name: '80%', value: 0.8},
                {name: '75%', value: 0.75},
              ]"
              option-label="name"
              option-value="value"
            />
          </div>
          <div class="flex flex-col gap-2 mb-4 max-w-96">
            <label>Glossaries to use:</label>
            <MultiSelect
              v-model="selectedGlossaries"
              class="w-96"
              placeholder="Select glossaries to use"
              :options="useGlossaryStore().glossaries"
              option-label="name"
              filter
              filter-placeholder="Search glossaries..."
            />
          </div>
          <MachineTranslationOptions v-model="mtOptions" />
        </div>
        <div v-else>
          {{ status }}
        </div>
      </template>
      <template #empty>
        <span v-if="!status">Choose a file to upload.</span>
      </template>
    </FileUpload>
  </div>
</template>
