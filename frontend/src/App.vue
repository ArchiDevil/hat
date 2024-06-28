<script setup lang="ts">
import {computed} from 'vue'
import {useRoute} from 'vue-router'

import PageNav from './components/PageNav.vue'

const route = useRoute()

const isLoginView = computed(() => {
  return route.name === 'login'
})
</script>

<template>
  <div class="content container">
    <PageNav v-if="!isLoginView" />
    <router-view />
  </div>
  <div
    id="modal"
    class="content"
  ></div>
</template>

<style scoped>
.content {
  @apply text-color font-medium font-sans;
}
</style>
