<script lang="ts">
import {defineComponent} from 'vue'

interface TmxFile {
  id: number
  name: string
}

interface XliffDoc {
  id: number
  name: string
}

export default defineComponent({
  data() {
    return {
      tmx_files: [] as TmxFile[],
      xliff_docs: [] as XliffDoc[],
    }
  },
  mounted() {
    this.loadTmxFiles()
    this.loadXliffDocs()
  },
  methods: {
    loadTmxFiles() {
      this.tmx_files = [
        {id: 1, name: 'test.tmx'},
        {id: 2, name: 'test2.tmx'},
      ]
    },
    loadXliffDocs() {
      this.xliff_docs = [
        {id: 1, name: 'test.xliff'},
        {id: 2, name: 'test2.xliff'},
      ]
    },
  },
})
</script>

<template>
  <div>
    <h1>Process TMX matches</h1>
    <div>
      <h1>TMX files list</h1>
      <form
        action="/tmx/upload"
        method="post"
        enctype="multipart/form-data"
        style="border: 1px solid grey; padding: 4px; width: 600px">
        <label for="tmx-file">Select a TMX file:</label>
        <input
          id="tmx-file"
          name="tmx-file"
          type="file"
          accept=".tmx" />
        <br />
        <button type="submit">Upload</button>
      </form>
      <ul id="tmx-files">
        <li v-for="file in tmx_files">
          <a :href="`/tmx/${file.id}`">#{{ file.id }} {{ file.name }}</a>
          <a :href="`/tmx/${file.id}/delete`"> [Delete file]</a>
        </li>
      </ul>
    </div>

    <div>
      <h1>XLIFF documents list</h1>
      <form
        action="/xliff/upload"
        method="post"
        enctype="multipart/form-data"
        style="border: 1px solid grey; padding: 4px; width: 600px">
        <label for="xliff-file">Select a XLIFF file:</label>
        <input
          id="xliff-file"
          name="xliff-file"
          type="file"
          accept=".xliff" />
        <br />
        <button type="submit">Upload</button>
      </form>
      <ul id="xliff-files">
        <li v-for="file in xliff_docs">
          <a :href="`/xliff/${file.id}`">#{{ file.id }} {{ file.name }}</a>
          <a :href="`/xliff/${file.id}/delete`"> [Delete file]</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped></style>
