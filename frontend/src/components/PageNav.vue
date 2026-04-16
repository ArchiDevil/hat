<script setup lang="ts">
import {useRouter} from 'vue-router'
import {storeToRefs} from 'pinia'

import {useUserStore} from '../stores/user'
import RoutingLink from './RoutingLink.vue'
import {isAdmin} from '../utilities/auth'

const router = useRouter()
const {currentUser} = storeToRefs(useUserStore())

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
    <div class="pt-8 flex flex-row gap-2">
      <p
        class="mr-4"
        :title="currentUser?.email"
      >
        <span class="text-surface-500">Logged as</span> {{ currentUser?.username }}
      </p>
      <RoutingLink
        class="uppercase font-semibold"
        name="home"
        title="Home"
      />
      <RoutingLink
        v-if="isAdmin()"
        class="uppercase font-semibold"
        name="users"
        title="Users"
      />
      <RoutingLink
        v-if="isAdmin()"
        class="uppercase font-semibold"
        name="tokens"
        title="Tokens"
      />
      <a
        href="#"
        class="uppercase font-semibold underline hover:decoration-2"
        @click="logout"
      >
        Logout
      </a>
    </div>
  </div>
</template>
