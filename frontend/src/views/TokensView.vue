<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {RegistrationTokenResponse} from '../client/schemas/RegistrationTokenResponse'
import {
  listTokens,
  createToken,
  deleteToken,
} from '../client/services/TokensService'

import {Button, DataTable, Column} from 'primevue'

import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'

const tokens = ref<RegistrationTokenResponse[]>()
const loading = ref(false)

const loadTokens = async () => {
  loading.value = true
  try {
    tokens.value = await listTokens()
  } finally {
    loading.value = false
  }
}

const handleCreateToken = async () => {
  await createToken()
  await loadTokens()
}

const handleDeleteToken = async (tokenId: number) => {
  await deleteToken(tokenId)
  await loadTokens()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const copyToClipboard = async (token: string) => {
  await navigator.clipboard.writeText(token)
}

onMounted(async () => {
  await loadTokens()
})
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle title="Registration Tokens" />
    <p class="mb-4 text-gray-600">
      Registration tokens allow new users to sign up. Share a token with someone
      to let them create an account.
    </p>
    <Button
      label="Create new token"
      icon="pi pi-plus"
      class="mt-2"
      @click="handleCreateToken"
    />
    <DataTable
      :value="tokens"
      :loading="loading"
      paginator
      :rows="10"
      :rows-per-page-options="[10, 25, 50]"
      table-style="w-full mt-4"
    >
      <Column
        field="id"
        header="Id"
        style="width: 80px"
      />
      <Column
        field="token"
        header="Token"
      >
        <template #body="slotProps">
          <div class="flex items-center gap-2">
            <code class="bg-gray-100 px-2 py-1 rounded text-sm break-all">
              {{ slotProps.data.token }}
            </code>
            <Button
              icon="pi pi-copy"
              severity="secondary"
              size="small"
              text
              @click="copyToClipboard(slotProps.data.token)"
            />
          </div>
        </template>
      </Column>
      <Column
        field="created_at"
        header="Created At"
      >
        <template #body="slotProps">
          {{ formatDate(slotProps.data.created_at) }}
        </template>
      </Column>
      <Column
        field="created_by"
        header="Created By"
        style="width: 120px"
      />
      <Column
        header="Actions"
        style="width: 100px"
      >
        <template #body="slotProps">
          <Button
            icon="pi pi-trash"
            severity="danger"
            size="small"
            text
            @click="handleDeleteToken(slotProps.data.id)"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
