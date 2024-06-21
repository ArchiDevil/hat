<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {User} from '../client/schemas/User'
import {getUsers} from '../client/services/UsersService'

import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

import PageTitle from '../components/PageTitle.vue'
import UserAddDialog from '../components/UserAddDialog.vue'
import UserEditDialog from '../components/UserEditDialog.vue'

const users = ref<User[]>()
const mode = ref<'table' | 'add' | 'edit'>('table')
const currentUser = ref<User>()

const editUser = async (user: User) => {
  mode.value = 'edit'
  currentUser.value = {...user}
}

const updateData = async () => {
  users.value = await getUsers()
  mode.value = 'table'
}

onMounted(async () => {
  await updateData()
})
</script>

<template>
  <div>
    <PageTitle title="Users page" />
    <template v-if="mode == 'table'">
      <Button
        label="Create new user"
        class="mt-2"
        @click="mode = 'add'"
      />
      <DataTable
        :value="users"
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        tableStyle="w-full mt-4"
      >
        <Column
          field="id"
          header="Id"
        ></Column>
        <Column
          field="username"
          header="Username"
        ></Column>
        <Column
          field="email"
          header="Email"
        ></Column>
        <Column
          field="role"
          header="Role"
        ></Column>
        <Column
          field="disabled"
          header="Disabled?"
        >
          <template #body="slotProps">
            <div class="flex items-baseline">
              <div class="flex-grow">
                {{ slotProps.data.disabled ? 'Yes' : 'No' }}
              </div>
              <Button
                class="ml-2"
                label="Edit"
                severity="secondary"
                size="small"
                @click="editUser(slotProps.data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </template>
    <template v-else-if="mode == 'add'">
      <UserAddDialog
        @create="updateData"
        @close="mode = 'table'"
      />
    </template>
    <template v-else-if="mode == 'edit'">
      <UserEditDialog
        :user="currentUser!"
        @finish="updateData"
        @close="mode = 'table'"
      />
    </template>
  </div>
</template>
