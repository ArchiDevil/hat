<script setup lang="ts">
import {ref} from 'vue'

import {UserToCreate} from '../client/schemas/UserToCreate'
import {createUser} from '../client/services/UsersService'

import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Password from 'primevue/password'

const emit = defineEmits<{
  create: []
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
  emit('create')
}
</script>

<template>
  <div class="border rounded border-slate p-4 mt-4 w-fit">
    <h2 class="font-bold text-xl mb-2">
      Create a new user
    </h2>
    <div class="flex flex-col gap-2 min-w-96">
      <div class="flex flex-col gap-2">
        <label class="text-color">Username</label>
        <InputText
          v-model="user.username"
          :disabled="loading"
        />
      </div>
      <div class="flex flex-col gap-2">
        <label class="text-color">Email</label>
        <InputText
          v-model="user.email"
          input-class="w-full"
          :disabled="loading"
          :feedback="false"
        />
      </div>
      <div class="flex flex-col gap-2">
        <label class="text-color">Password</label>
        <Password
          v-model="user.password"
          input-class="w-full"
          :disabled="loading"
          :feedback="false"
        />
      </div>
      <div class="flex flex-col gap-2">
        <label>Role</label>
        <Select
          v-model="user.role"
          :options="[
            {value: 'user', name: 'User'},
            {value: 'admin', name: 'Administrator'},
          ]"
          option-label="name"
          option-value="value"
          placeholder="Select a role"
        />
      </div>
      <div class="flex items-center">
        <Checkbox
          id="enabled"
          v-model="user.disabled"
          :binary="true"
          :disabled="loading"
        />
        <label
          for="enabled"
          class="ml-2"
        >
          Disabled
        </label>
      </div>
    </div>
    <div class="flex gap-2 mt-2">
      <Button
        label="Create"
        :disabled="loading"
        @click="create"
      />
      <Button
        label="Close"
        :disabled="loading"
        @click="$emit('close')"
      />
    </div>
  </div>
</template>
