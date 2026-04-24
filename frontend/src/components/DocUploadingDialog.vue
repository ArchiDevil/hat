<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {MandeError} from 'mande'
import {
  FileUpload,
  FileUploadSelectEvent,
  Select,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  InputText,
  Button,
} from 'primevue'

import {
  createDoc,
  processDoc,
  matchDoc,
} from '../client/services/DocumentService'
import {Document} from '../client/schemas/Document'

import MachineTranslationOptions, {
  MtType,
} from './MachineTranslationOptions.vue'

const emit = defineEmits<{
  uploaded: []
  processed: [fileId: number]
  matched: [fileId: number]
}>()

const props = defineProps<{
  title: string
  projectId: number
}>()

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

const uploadedFile = ref(null) as Ref<Document | null>
const processingAvailable = computed(() => uploadedFile.value != null)
const uploading = ref(false)
const status = ref('')

const activeTab = ref('process')
const matchFile = ref(null) as Ref<Blob | null>
const matchApiKey = ref('')

const createFile = async (event: FileUploadSelectEvent) => {
  status.value = ''
  if (!event.files) {
    return
  }

  const selectedFile = (event.files as File[])[0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    uploadedFile.value = await createDoc({
      file: selectedFile,
      project_id: props.projectId,
    })
    uploading.value = false
    status.value = 'Ready for processing'
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

const onMatchFileSelect = (event: FileUploadSelectEvent) => {
  if (!event.files) {
    return
  }
  matchFile.value = (event.files as File[])[0]
}

const similarityThreshold = ref<number>(1.0)

const startProcessing = async () => {
  if (!processingAvailable.value) {
    return
  }

  status.value = ''

  try {
    uploading.value = true
    status.value = 'Processing...'
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

const startMatching = async () => {
  if (!processingAvailable.value) {
    return
  }
  if (!matchFile.value) {
    status.value = 'Select a file to match against'
    return
  }
  if (!matchApiKey.value) {
    status.value = 'Enter an API key'
    return
  }

  status.value = ''

  try {
    uploading.value = true
    status.value = 'Matching...'
    await matchDoc(uploadedFile.value!.id, {
      file_to_match: matchFile.value,
      api_key: matchApiKey.value,
    })
    uploading.value = false
    status.value = 'Done!'
    emit('matched', uploadedFile.value!.id)
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

const handleAction = async () => {
  if (activeTab.value === 'match') {
    await startMatching()
  } else {
    await startProcessing()
  }
}
</script>

<template>
  <div class="min-w-96">
    <FileUpload
      mode="advanced"
      custom-upload
      accept=".xliff,.txt"
      :disabled="uploading"
      @select="createFile"
      @uploader="handleAction"
    >
      <template #content="{files}">
        <div v-if="files.length != 0">
          <Tabs v-model:value="activeTab">
            <TabList>
              <Tab value="process">
                Process
              </Tab>
              <Tab value="match">
                Match
              </Tab>
            </TabList>
            <TabPanels>
              <TabPanel value="process">
                <p class="font-semibold">
                  Processing options
                </p>
                <div class="flex flex-col gap-2 mb-4 max-w-96 mt-2">
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
                <MachineTranslationOptions v-model="mtOptions" />
              </TabPanel>
              <TabPanel value="match">
                <p class="font-semibold">
                  Match options
                </p>
                <div class="flex flex-col gap-3 mt-2">
                  <FileUpload
                    mode="advanced"
                    custom-upload
                    accept=".txt"
                    :disabled="uploading"
                    :auto="false"
                    @select="onMatchFileSelect"
                  >
                    <template #header="{chooseCallback}">
                      <Button
                        label="Choose"
                        icon="pi pi-plus"
                        :disabled="uploading"
                        @click="chooseCallback()"
                      />
                    </template>
                    <template #content="slotProps">
                      <div v-if="slotProps.files.length > 0">
                        <span>{{ slotProps.files[0].name }}</span>
                      </div>
                    </template>
                    <template #empty>
                      <span>Choose a file to match against.</span>
                    </template>
                  </FileUpload>
                  <div class="flex flex-col gap-1">
                    <label>API Key</label>
                    <InputText
                      v-model="matchApiKey"
                      :disabled="uploading"
                    />
                  </div>
                </div>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
        <div v-else>
          {{ status }}
        </div>
      </template>
      <template #empty>
        <span v-if="!status">
          Choose a file to upload into the project.
        </span>
      </template>
    </FileUpload>
  </div>
</template>
