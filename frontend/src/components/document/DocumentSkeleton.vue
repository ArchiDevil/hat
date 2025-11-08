<script setup lang="ts">
import Skeleton from 'primevue/skeleton'
import RoutingLink from '../RoutingLink.vue'
import LoadingMessage from './LoadingMessage.vue'
</script>

<template>
  <div class="ml-8 mt-4 flex flex-col gap-2">
    <Skeleton
      width="20rem"
      height="2rem"
    />
    <Skeleton
      width="10rem"
      height="1.2rem"
    />
    <Skeleton
      width="16rem"
      height="1.2rem"
    />
    <Skeleton
      width="8rem"
      height="1.2rem"
    />
    <RoutingLink
      name="home"
      title="Return to main page"
    />
    <LoadingMessage class="max-w-[600px]" />
  </div>
</template>
