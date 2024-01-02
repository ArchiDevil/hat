<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {apiAccessor} from '../api'
import {defaults} from 'mande'
import Button from './Button.vue'

const emit = defineEmits(['uploaded'])
const props = defineProps(['title', 'extension', 'url'])

const file = ref(null) as Ref<File | null>
const input = ref(null)
const uploadAvailable = computed(() => file.value != null)
const uploading = ref(false)
const status = ref()

const updateFiles = () => {
  status.value = undefined
  const element = input.value as unknown as HTMLInputElement
  if (!element.files) {
    return
  }
  file.value = element.files[0]
}

const uploadFile = async () => {
  if (!uploadAvailable) {
    return
  }

  const element = input.value as unknown as HTMLInputElement
  const attachedFile = element.files![0]

  const formData = new FormData()
  formData.append('file', attachedFile)
  // this is a workaround for a bug in mande
  const defaultHeaders = defaults.headers
  try {
    const api = apiAccessor(props.url)
    defaults.headers = {}
    uploading.value = true
    status.value = 'Uploading...'
    const response = await api.post('', formData)
    uploading.value = false
    status.value = 'Done!'
    emit('uploaded', response)
  } catch (error: any) {
    uploading.value = false
    status.value = `${error.message} :(`
  } finally {
    defaults.headers = defaultHeaders
  }
}
</script>

<template>
  <div class="p-2 min-w-96 border border-slate-500">
    <label
      for="file"
      class="font-semibold mr-2">
      {{ title }}
    </label>
    <input
      id="file-input"
      type="file"
      ref="input"
      @change="updateFiles"
      :accept="extension" />
    <Button
      class="ml-2"
      @click="uploadFile"
      :disabled="!uploadAvailable || uploading">
      Upload
    </Button>
    <span
      class="ml-2"
      v-if="status">
      {{ status }}
    </span>
  </div>
</template>
