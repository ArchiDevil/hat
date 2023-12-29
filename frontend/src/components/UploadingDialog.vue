<script lang="ts">
import {defineComponent} from 'vue'
import Button from './Button.vue'
import {mande} from 'mande'

export default defineComponent({
  components: {Button},
  emits: ['uploaded'],
  props: ['title', 'extension', 'url'],
  methods: {
    async uploadFile() {
      const formData = new FormData()
      formData.append(
        'file',
        (document.getElementById('file-input') as HTMLInputElement).files![0]
      )
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
  },
})
</script>

<template>
  <div>
    <label
      for="file"
      class="font-semibold mr-2">
      {{ title }}
    </label>
    <input
      id="file-input"
      type="file"
      accept=".tmx" />
    <Button @click="uploadFile">Upload</Button>
  </div>
</template>

<style scoped>
div {
  @apply p-2 min-w-96;
  @apply border border-slate-500 border-solid;
}
</style>
