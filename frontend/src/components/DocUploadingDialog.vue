<script setup lang="ts">
import {Ref, ref, computed, onMounted} from 'vue'
import {MandeError} from 'mande'

import {
  createDoc,
  processDoc,
  setGlossaries,
} from '../client/services/DocumentService'
import {Document} from '../client/schemas/Document'
import {MachineTranslationSettings} from '../client/schemas/MachineTranslationSettings'
import {TranslationMemoryUsage} from '../client/schemas/TranslationMemoryUsage'

import {useTmStore} from '../stores/tm'
import {useGlossaryStore} from '../stores/glossary'

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

const uploadedFile = ref(null) as Ref<Document | null>
const uploading = ref(false)
const status = ref('')

const substituteNumbers = ref(false)
const useMachineTranslation = ref(false)
const machineTranslationSettings = ref<MachineTranslationSettings>({
  folder_id: '',
  oauth_token: '',
})
const similarityThreshold = ref<number>(1.0)

const processingAvailable = computed(() => uploadedFile.value != null)
const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const memoryMode = ref<TranslationMemoryUsage>('newest')

const createFile = async (event: FileUploadSelectEvent) => {
  status.value = ''
  if (!event.files) {
    return
  }

  const selectedFile = event.files[0] as File

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
    await setGlossaries(uploadedFile.value!.id, {
      glossaries: selectedGlossaries.value.map((g) => {
        return {id: g.id}
      }),
    })
    await processDoc(uploadedFile.value!.id, {
      substitute_numbers: substituteNumbers.value,
      machine_translation_settings: useMachineTranslation.value
        ? machineTranslationSettings.value
        : null,
      memory_ids: selectedTms.value.map((tm) => tm.id),
      memory_usage: memoryMode.value,
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
              v-model="selectedTms"
              placeholder="Select TMX files to use"
              :options="tmStore.memories"
              optionLabel="name"
              filter
              filterPlaceholder="Search TMX files..."
            />
          </div>
          <div class="flex flex-col gap-2 mb-4 max-w-96">
            <label>When segment is found in multiple TMXs:</label>
            <Select
              v-model="memoryMode"
              :options="[
                {name: 'Use newest TM', value: 'newest'},
                {name: 'Use oldest TM', value: 'oldest'},
              ]"
              option-label="name"
              option-value="value"
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
          <div class="flex items-center mb-4">
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
              Substitute segments containing only digits
            </label>
          </div>
          <div class="flex flex-col gap-2 mb-4 max-w-96">
            <label>Glossaries to use:</label>
            <MultiSelect
              class="w-96"
              v-model="selectedGlossaries"
              placeholder="Select glossaries to use"
              :options="useGlossaryStore().glossaries"
              optionLabel="name"
              filter
              filterPlaceholder="Search glossaries..."
            />
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
      <template #empty>
        <span v-if="!status">Choose a file to upload.</span>
      </template>
    </FileUpload>
  </div>
</template>
