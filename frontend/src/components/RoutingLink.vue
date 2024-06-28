<script setup lang="ts">
import {RouteParamsRaw} from 'vue-router'

defineProps<{
  name: string
  params?: RouteParamsRaw
}>()
</script>

<template>
  <router-link
    :to="{name: name, params: params}"
    class="decoration-slate-900 transition-colors underline decoration-1 hover:decoration-2"
  >
    <slot></slot>
  </router-link>
</template>
