<script lang="ts">
import {defineComponent} from 'vue'
import {mande} from 'mande'
import Button from './Button.vue'

export default defineComponent({
  components: {Button},
  emits: ['uploaded'],
  props: ['title', 'extension', 'url'],
  data() {
    return {
      file: null as File | null,
    }
  },
  computed: {
    uploadAvailable() {
      return this.file != null
    },
  },
  methods: {
    async uploadFile() {
      if (!this.uploadAvailable) {
        return
      }

      const formData = new FormData()
      const input = this.$refs.input as HTMLInputElement
      const attachedFile = input.files![0]
      formData.append('file', attachedFile)
      try {
        const response = await mande(this.url).post('', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        this.$emit('uploaded', response)
      } catch (error) {
        console.error(error)
      }
    },
    updateFiles() {
      const input = this.$refs.input as HTMLInputElement
      if (!input.files) {
        return
      }
      this.file = input.files[0]
    },
  },
})
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
