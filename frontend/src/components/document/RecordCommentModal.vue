<script setup lang="ts">
import {computed, ref} from 'vue'
import {useQuery, useQueryCache} from '@pinia/colada'

import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'

import {createComment, getComments} from '../../client/services/RecordsService'
import {CommentResponse} from '../../client/schemas/CommentResponse'

const props = defineProps<{
  recordId: number
}>()

const emit = defineEmits<{
  addComment: []
}>()

const visible = defineModel<boolean>()
const mode = ref<'observe' | 'add'>('observe')

const commentsKey = computed(() => ['comments', props.recordId])
const {data, isLoading} = useQuery({
  key: commentsKey,
  query: async () => {
    return await getComments(props.recordId)
  },
  enabled: () => props.recordId !== -1,
  placeholderData: <T,>(prevData: T) => prevData,
  staleTime: 60 * 1000,
})

const commentAdding = ref(false)
const queryCache = useQueryCache()
const newCommentText = ref('')
const addComment = async () => {
  commentAdding.value = true
  await createComment(props.recordId, {
    text: newCommentText.value,
  })
  window.umami.track('comment-add')
  newCommentText.value = ''
  mode.value = 'observe'
  await queryCache.invalidateQueries({key: commentsKey.value})
  commentAdding.value = false
  emit('addComment')
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="`Comments for ${recordId}`"
    :style="{width: '56rem'}"
  >
    <Button
      class="mb-2"
      severity="primary"
      size="small"
      label="Add new"
      @click="mode = 'add'"
    />
    <div v-if="mode == 'observe'">
      <DataTable
        v-if="!isLoading && data !== undefined && data.length > 0"
        :value="data"
      >
        <Column
          field="text"
          header="Text"
        />
        <Column
          :field="(record: CommentResponse) => record.created_by_user.username"
          header="Made by"
        />
        <Column
          :field="
            (record: CommentResponse) =>
              new Date(record.updated_at).toLocaleString()
          "
          header="Last updated"
        />
      </DataTable>
      <ProgressSpinner v-else-if="isLoading" />
      <div
        v-else
        class="text-center py-4"
      >
        <i class="pi pi-pencil text-2xl text-gray-400" />
        <p class="mt-2 text-gray-600">
          No comments for the segment
        </p>
      </div>
    </div>
    <div
      v-if="mode == 'add'"
      class="flex flex-col gap-4"
    >
      <div class="flex items-center gap-2">
        <label
          for="text"
          class="font-semibold w-24"
        >
          Text
        </label>
        <InputText
          v-model="newCommentText"
          class="flex-auto"
          autocomplete="off"
          placeholder="Input comment"
          :disabled="commentAdding"
        />
      </div>
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          :disabled="commentAdding"
          @click="
            () => {
              newCommentText = ''
              mode = 'observe'
            }
          "
        />
        <Button
          type="button"
          label="Add"
          :loading="commentAdding"
          @click="addComment"
        />
      </div>
    </div>
  </Dialog>
</template>
