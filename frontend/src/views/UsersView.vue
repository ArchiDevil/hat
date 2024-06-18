<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {User} from '../client/schemas/User'
import {getUsers} from '../client/services/UsersService'

import PageTitle from '../components/PageTitle.vue'
import AppButton from '../components/AppButton.vue'
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
      <AppButton
        class="mt-2"
        @click="mode = 'add'"
        >Create new user</AppButton
      >
      <table class="mt-4 w-full">
        <thead>
          <tr class="text-left">
            <th>Id</th>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Disabled?</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            class="hover:bg-slate-200"
          >
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.role }}</td>
            <td>
              <div class="flex items-baseline">
                <div class="flex-grow">{{ user.disabled ? 'Yes' : 'No' }}</div>
                <AppButton
                  @click="editUser(user)"
                  class="ml-2"
                >
                  Edit
                </AppButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
    <template v-else-if="mode == 'add'">
      <UserAddDialog
        @created="updateData"
        @closed="mode = 'table'"
      />
    </template>
    <template v-else-if="mode == 'edit'">
      <UserEditDialog
        :user="currentUser!"
        @finished="updateData"
        @closed="mode = 'table'"
      />
    </template>
  </div>
</template>

<style scoped>
tr {
  @apply border-b-2;
}

td,
th {
  @apply px-2 py-1;
}
</style>
