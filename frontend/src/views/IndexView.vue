<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {deleteTmx, getTmxs} from '../client/services/TmxService'
import {deleteXliff, getXliffs} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {TmxFile} from '../client/schemas/TmxFile'

import File from '../components/File.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import XliffUploadingDialog from '../components/XliffUploadingDialog.vue'
import SupportLinks from '../components/SupportLinks.vue'
import PageTitle from '../components/PageTitle.vue'
import RoutingLink from '../components/RoutingLink.vue'

const tmxDocs = ref<TmxFile[]>([])
const xliffDocs = ref<XliffFile[]>([])

const getTmxDocs = async () => {
  tmxDocs.value = await getTmxs()
}

const getXliffDocs = async () => {
  xliffDocs.value = await getXliffs()
}

onMounted(async () => {
  await getTmxDocs()
  await getXliffDocs()
})
</script>

<template>
  <div>
    <div class="flex items-baseline">
      <PageTitle
        class="flex-grow"
        title="Human Assisted Translation project"
      />
      <div class="pt-8">
        <RoutingLink class="mx-2 uppercase font-semibold" href="/">Home</RoutingLink>
        <RoutingLink class="mx-2 uppercase font-semibold" href="/users/">Users</RoutingLink>
      </div>
    </div>
    <div class="w-1/2 border rounded bg-red-50 p-4">
      <p>
        The tool is currently in a testing phase. Please, be ready to sudden
        breakups and unexpected crashes.
        <span class="text-red-700 font-semibold">
          Use small portions of data with Yandex first!
        </span>
        If you find any bug or have ideas, please report them in any form using
        these links:
      </p>
      <SupportLinks />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">TMX files list</h2>
      <TmxUploadingDialog
        title="Select a TMX file:"
        @uploaded="getTmxDocs()"
      />
      <File
        v-for="file in tmxDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteTmx"
        type="tmx"
        @delete="getTmxDocs()"
      />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">XLIFF documents list</h2>
      <XliffUploadingDialog
        title="Select a XLIFF file:"
        @processed="(fileId) => $router.push(`/xliff/${fileId}`)"
      />
      <File
        v-for="file in xliffDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteXliff"
        type="xliff"
        @delete="getXliffDocs()"
      />
    </div>
  </div>
</template>
