<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  props: ['href'],
})
</script>

<template>
  <a
    :href="href"
    class="py-1 px-2 text-slate-900 hover:text-slate-950 transition-colors decoration-slate-950 underline decoration-1 hover:decoration-2">
    <slot></slot>
  </a>
</template>

<style scoped></style>
