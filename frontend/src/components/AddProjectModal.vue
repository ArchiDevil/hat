<script setup lang="ts">
import {ref} from 'vue'
import {useQueryCache} from '@pinia/colada'
import {Button, Dialog, InputText} from 'primevue'
import {createProject} from '../client/services/ProjectsService'
import {PROJECT_KEYS} from '../queries/projects'

const visible = defineModel<boolean>({required: true})

const queryCache = useQueryCache()

const name = ref('')
const addProject = async () => {
  await createProject({
    name: name.value,
  })
  await queryCache.invalidateQueries({
    key: PROJECT_KEYS.root,
  })
  visible.value = false
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Add new project"
    :style="{width: '25rem'}"
  >
    <template #default>
      <div class="flex items-center gap-2">
        <label
          for="username"
          class="font-semibold w-24"
        >
          Name
        </label>
        <InputText
          id="username"
          v-model="name"
          class="flex-auto"
          autocomplete="off"
        />
      </div>
    </template>
    <template #footer>
      <Button
        label="Cancel"
        severity="secondary"
        autofocus
        @click="visible = false"
      />
      <Button
        label="Add"
        autofocus
        @click="() => addProject()"
      />
    </template>
  </Dialog>
</template>
