<script lang="ts">
import {defineComponent} from 'vue'
import {mande} from 'mande'

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
  async mounted() {
    this.tmx_files = await mande('/api/tmx').get<TmxFile[]>()
    this.xliff_docs = await mande('/api/xliff').get<XliffDoc[]>()
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
        class="form">
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
        class="form">
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

<style scoped>
.form {
  border: 2px solid grey;
  padding: 8px;
  width: 600px;
}
</style>
