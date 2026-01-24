<script setup lang="ts">
import {useRouter} from 'vue-router'

import {useUserStore} from '../stores/user'

import RoutingLink from './RoutingLink.vue'

const router = useRouter()

const logout = async () => {
  await useUserStore().logout()
  await router.push({name: 'login'})
}
</script>

<template>
  <div class="flex items-baseline">
    <div class="text-lg grow uppercase">
      Human Assisted Translation project
    </div>
    <div class="pt-8">
      <RoutingLink
        class="mx-2 uppercase font-semibold"
        name="home"
        title="Home"
      />
      <RoutingLink
        v-if="useUserStore().currentUser?.role === 'admin'"
        class="mx-2 uppercase font-semibold"
        name="users"
        title="Users"
      />
      <a
        href="#"
        class="mx-2 uppercase font-semibold underline hover:decoration-2"
        @click="logout"
      >
        Logout
      </a>
    </div>
  </div>
</template>
