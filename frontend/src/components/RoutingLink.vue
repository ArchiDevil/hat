<script setup lang="ts">
defineProps(['href'])
</script>

<template>
  <router-link
    :to="href"
    class="decoration-slate-900 transition-colors underline decoration-1 hover:decoration-2">
    <slot></slot>
  </router-link>
</template>
