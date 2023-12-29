<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {mande} from 'mande'
import Button from './Button.vue'

const emit = defineEmits(['uploaded'])
const props = defineProps(['title', 'extension', 'url'])

const file = ref(null) as Ref<File | null>
const input = ref(null)
const uploadAvailable = computed(() => file.value != null)

const updateFiles = () => {
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

  const formData = new FormData()
  const element = input as unknown as HTMLInputElement
  const attachedFile = element.files![0]
  formData.append('file', attachedFile)
  try {
    const response = await mande(props.url).post('', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    emit('uploaded', response)
  } catch (error) {
    console.error(error)
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
      @click="uploadFile"
      :disabled="!uploadAvailable">
      Upload
    </Button>
  </div>
</template>
