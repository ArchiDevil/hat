<script setup lang="ts">
import {computed, ref} from 'vue'

import {GlossaryResponse} from '../../client/schemas/GlossaryResponse'

import Button from 'primevue/button'
import RoutingLink from '../RoutingLink.vue'
import EditGlossaryDialog from './EditGlossaryDialog.vue'
import {getDownloadGlossaryCsvLink} from '../../client/services/GlossaryService'
import {isAdmin} from '../../utilities/auth'

defineEmits<{
  update: []
}>()

const {file} = defineProps<{
  file: GlossaryResponse
}>()

const editDialogVisible = ref(false)
const downloadLink = computed(() => getDownloadGlossaryCsvLink(file.id))
</script>

<template>
  <div
    class="my-1 py-1 px-2 border flex gap-8 items-baseline rounded-border border-surface bg-surface-50"
  >
    <div class="w-[24rem] truncate">
      <RoutingLink
        name="glossary"
        :params="{id: file.id}"
        :title="file.name"
      >
        #{{ file.id }} {{ file.name ?? 'No name' }}
      </RoutingLink>
    </div>
    <Button
      v-if="isAdmin()"
      label="Edit"
      severity="secondary"
      @click="editDialogVisible = true"
    />
    <a
      v-if="isAdmin()"
      :href="downloadLink"
      class="underline hover:decoration-2"
    >
      Download as CSV file
    </a>
    <EditGlossaryDialog
      v-model="editDialogVisible"
      :glossary-id="file.id"
      @close="$emit('update')"
    />
  </div>
</template>
