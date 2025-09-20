<script setup lang="ts">
import {ref} from 'vue'

import {GlossaryResponse} from '../../client/schemas/GlossaryResponse'

import Button from 'primevue/button'
import RoutingLink from '../RoutingLink.vue'
import EditGlossaryDialog from './EditGlossaryDialog.vue'

defineEmits<{
  update: []
}>()

defineProps<{
  file: GlossaryResponse
}>()

const editDialogVisible = ref(false)
</script>

<template>
  <div
    class="my-1 py-1 px-2 border flex gap-8 items-baseline rounded-border border-surface bg-surface-50"
  >
    <div
      class="w-[24rem] text-ellipsis whitespace-nowrap overflow-hidden"
      :title="file.name"
    >
      #{{ file.id }} {{ file.name ?? 'No name' }}
    </div>
    <RoutingLink
      name="glossary"
      :params="{id: file.id}"
      title="Open"
    />
    <Button
      label="Edit"
      severity="secondary"
      @click="editDialogVisible = true"
    />
    <EditGlossaryDialog
      v-model="editDialogVisible"
      :glossary-id="file.id"
      @close="$emit('update')"
    />
  </div>
</template>
