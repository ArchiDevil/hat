<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useQuery, useQueryCache} from '@pinia/colada'

import {
  Button,
  DataTable,
  Column,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
} from 'primevue'

import {User} from '../client/schemas/User'
import {
  listTokens,
  createToken,
  deleteToken,
} from '../client/services/TokensService'
import {
  listTokens as listApiTokens,
  deleteToken as deleteApiToken,
} from '../client/services/ApitokensService'
import {getUsers} from '../client/services/UsersService'

import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'
import ApiTokenCreateDialog from '../components/ApiTokenCreateDialog.vue'

import {copyToClipboard} from '../utilities/clipboard'

const queryCache = useQueryCache()

const {data: registrationTokens, isLoading: registrationLoading} = useQuery({
  key: ['registration-tokens'],
  query: async () => {
    return await listTokens()
  },
})

const {data: apiTokens, isLoading: apiLoading} = useQuery({
  key: ['api-tokens'],
  query: async () => {
    return await listApiTokens()
  },
})

const users = ref<User[]>([])
const userMap = ref<Map<number, User>>(new Map())
const loadUsers = async () => {
  users.value = await getUsers()
  userMap.value = new Map(users.value.map((u) => [u.id, u]))
}

const handleCreateToken = async () => {
  await createToken()
  await queryCache.invalidateQueries({
    key: ['registration-tokens'],
  })
}

const handleDeleteToken = async (tokenId: number) => {
  await deleteToken(tokenId)
  await queryCache.invalidateQueries({
    key: ['registration-tokens'],
  })
}

const handleDeleteApiToken = async (tokenId: number) => {
  await deleteApiToken(tokenId)
  await queryCache.invalidateQueries({
    key: ['api-tokens'],
  })
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleString()
}

const getUserName = (userId: number) => {
  return userMap.value.get(userId)?.username ?? String(userId)
}

onMounted(async () => {
  await Promise.all([loadUsers()])
})

const showCreateApiToken = ref(false)
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle title="Tokens" />
    <Tabs value="registration">
      <TabList>
        <Tab value="registration">
          Registration Tokens
        </Tab>
        <Tab value="api">
          API Tokens
        </Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="registration">
          <p class="mb-4 text-gray-600">
            Registration tokens allow new users to sign up. Share a token with
            someone to let them create an account.
          </p>
          <Button
            label="Create New Token"
            icon="pi pi-plus"
            class="mt-2"
            @click="handleCreateToken"
          />
          <DataTable
            :value="registrationTokens"
            :loading="registrationLoading"
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
        </TabPanel>

        <TabPanel value="api">
          <p class="mb-4 text-gray-600">
            API tokens allow programmatic access to the API for a specific user.
            The token value is only shown once at creation time.
          </p>
          <template v-if="!showCreateApiToken">
            <Button
              label="Create API Token"
              icon="pi pi-plus"
              class="mt-2"
              @click="showCreateApiToken = true"
            />
          </template>
          <template v-else>
            <ApiTokenCreateDialog
              @create="
                () =>
                  queryCache.invalidateQueries({
                    key: ['api-tokens'],
                  })
              "
              @close="showCreateApiToken = false"
            />
          </template>
          <DataTable
            :value="apiTokens"
            :loading="apiLoading"
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
              field="name"
              header="Name"
            />
            <Column
              field="user_id"
              header="User"
            >
              <template #body="slotProps">
                {{ getUserName(slotProps.data.user_id) }}
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
              field="expires_at"
              header="Expires At"
            >
              <template #body="slotProps">
                {{ formatDate(slotProps.data.expires_at) }}
              </template>
            </Column>
            <Column
              field="last_used_at"
              header="Last Used"
            >
              <template #body="slotProps">
                {{ formatDate(slotProps.data.last_used_at) }}
              </template>
            </Column>
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
                  @click="handleDeleteApiToken(slotProps.data.id)"
                />
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>
