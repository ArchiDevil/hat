<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {Button, InputText, Select} from 'primevue'

import {User} from '../client/schemas/User'
import {ApiTokenCreatedResponse} from '../client/schemas/ApiTokenCreatedResponse'
import {getUsers} from '../client/services/UsersService'
import {createToken as createApiToken} from '../client/services/ApitokensService'
import {copyToClipboard} from '../utilities/clipboard'

const expirationOptions = [
  {label: 'No expiration', value: null},
  {label: '1 day', value: 86400000},
  {label: '1 week', value: 604800000},
  {label: '1 month', value: 2592000000},
  {label: '1 year', value: 31536000000},
]

const emit = defineEmits<{
  create: []
  close: []
}>()

const users = ref<User[]>([])
const loadUsers = async () => {
  users.value = await getUsers()
}

const expiration = ref<number | null>(null)
const getExpiresAt = () => {
  if (expiration.value === null) return null
  return new Date(Date.now() + expiration.value).toISOString()
}

const name = ref('')
const userId = ref<number | null>(null)
const loading = ref(false)
const createdToken = ref<ApiTokenCreatedResponse | null>(null)
const create = async () => {
  if (!userId.value) return
  loading.value = true
  try {
    createdToken.value = await createApiToken({
      name: name.value,
      user_id: userId.value,
      expires_at: getExpiresAt(),
    })
    emit('create')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadUsers()
})
</script>

<template>
  <div class="border rounded border-surface p-4 mt-4 w-fit">
    <h2 class="font-bold text-xl mb-2">
      Create API Token
    </h2>
    <template v-if="!createdToken">
      <div class="flex flex-col gap-2 min-w-96">
        <div class="flex flex-col gap-2">
          <label class="text-color">Name</label>
          <InputText
            v-model="name"
            :disabled="loading"
            placeholder="Token name"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-color">User</label>
          <Select
            v-model="userId"
            :options="users"
            option-label="username"
            option-value="id"
            placeholder="Select a user"
            :disabled="loading"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-color">Expires At</label>
          <Select
            v-model="expiration"
            :options="expirationOptions"
            option-label="label"
            option-value="value"
            placeholder="Select expiration"
            :disabled="loading"
          />
        </div>
      </div>
      <div class="flex gap-2 mt-2">
        <Button
          label="Create"
          :disabled="loading || !name || !userId"
          @click="create"
        />
        <Button
          label="Close"
          :disabled="loading"
          @click="$emit('close')"
        />
      </div>
    </template>
    <template v-else>
      <div class="flex flex-col gap-2">
        <p>
          API token created successfully. Copy the token now — it won't be shown
          again.
        </p>
        <div class="flex items-center gap-2">
          <code class="bg-gray-100 px-2 py-1 rounded break-all">
            {{ createdToken.token }}
          </code>
          <Button
            icon="pi pi-copy"
            severity="secondary"
            size="small"
            text
            @click="copyToClipboard(createdToken!.token)"
          />
        </div>
      </div>
      <div class="flex gap-2 mt-2">
        <Button
          label="Close"
          @click="$emit('close')"
        />
      </div>
    </template>
  </div>
</template>
