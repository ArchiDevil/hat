<script setup lang="ts">
import {ref} from 'vue'

import {UserToCreate} from '../client/schemas/UserToCreate'
import {createUser} from '../client/services/UsersService'

import AppButton from './AppButton.vue'
import LabeledTextInput from './LabeledTextInput.vue'
import AppCheckbox from './AppCheckbox.vue'
import AppSelect from './AppSelect.vue'

const emit = defineEmits<{
  created: []
  close: []
}>()

const user = ref<UserToCreate>({
  email: '',
  username: '',
  password: '',
  role: 'user',
  disabled: false,
})

const loading = ref(false)

const create = async () => {
  loading.value = true
  await createUser(user.value)
  loading.value = false
  emit('created')
}
</script>

<template>
  <div class="border rounded border-slate p-4 mt-4 w-fit">
    <h2 class="font-bold text-xl mb-2">Create a new user</h2>
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
      <LabeledTextInput
        title="Password"
        v-model="user.password"
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
        @click="create"
        :disabled="loading"
        >Create</AppButton
      >
      <AppButton
        @click="$emit('close')"
        :disabled="loading"
        >Close</AppButton
      >
    </div>
  </div>
</template>
