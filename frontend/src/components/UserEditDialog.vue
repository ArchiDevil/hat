<script setup lang="ts">
import {ref} from 'vue'

import {updateUser} from '../client/services/UsersService'
import {User} from '../client/schemas/User'

import AppButton from './AppButton.vue'
import LabeledTextInput from './LabeledTextInput.vue'
import AppCheckbox from './AppCheckbox.vue'
import AppSelect from './AppSelect.vue'

const emit = defineEmits<{
  finished: []
  closed: []
}>()

const props = defineProps<{
  user: User
}>()

const loading = ref(false)

const update = async () => {
  loading.value = true
  await updateUser(props.user.id, props.user)
  loading.value = false
  emit('finished')
}
</script>

<template>
  <div class="border rounded border-slate p-4 mt-4 w-fit">
    <h2 class="font-bold text-xl mb-2">Edit a user</h2>
    <div class="flex flex-col gap-2">
      <LabeledTextInput
        title="Username"
        v-model="user.username"
        :disabled="loading"
      />
      <LabeledTextInput
        title="Email"
        v-model="user.email"
        :disabled="loading"
      />
      <AppSelect
        title="Role"
        :options="[
          {value: 'user', name: 'User'},
          {value: 'admin', name: 'Administrator'},
        ]"
        :disabled="loading"
      />
      <AppCheckbox
        title="Disabled"
        v-model="user.disabled"
        :disabled="loading"
      />
    </div>
    <div class="flex gap-2 mt-2">
      <AppButton
        @click="update"
        :disabled="loading"
      >
        Update
      </AppButton>
      <AppButton
        @click="$emit('closed')"
        :disabled="loading"
      >
        Close
      </AppButton>
    </div>
  </div>
</template>
