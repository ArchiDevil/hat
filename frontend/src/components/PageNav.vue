<script setup lang="ts">
import {useRouter} from 'vue-router'

import {useUserStore} from '../stores/user'

import PageTitle from './PageTitle.vue'
import RoutingLink from './RoutingLink.vue'

const router = useRouter()

const logout = async () => {
  await useUserStore().logout()
  router.push({name: 'login'})
}
</script>

<template>
  <div class="flex items-baseline">
    <PageTitle
      class="flex-grow"
      title="Human Assisted Translation project"
    />
    <div class="pt-8">
      <RoutingLink
        class="mx-2 uppercase font-semibold"
        name="home"
      >
        Home
      </RoutingLink>
      <RoutingLink
        v-if="useUserStore().currentUser?.role === 'admin'"
        class="mx-2 uppercase font-semibold"
        name="users"
      >
        Users
      </RoutingLink>
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
