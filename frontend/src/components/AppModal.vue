<script setup lang="ts">
import {Teleport} from 'vue'

const props = defineProps<{open: boolean}>()
</script>

<template>
  <Teleport to="#modal">
    <div
      class="fixed top-0 left-0 z-40 bg-slate-500 bg-opacity-60 w-dvw h-dvh"
      v-if="open"
    ></div>
    <div
      class="border bg-gray-100 fixed z-50 top-20 left-1/2 w-96 -ml-48"
      v-if="open"
    >
      <slot></slot>
    </div>
  </Teleport>
</template>
