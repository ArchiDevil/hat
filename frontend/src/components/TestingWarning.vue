<script setup lang="ts">
import Panel from 'primevue/panel'
import SupportLinks from '../components/SupportLinks.vue'
</script>

<template>
  <Panel
    class="w-1/2 border border-surface rounded bg-red-50 px-4 mt-4"
    header="Warning!"
    toggleable
  >
    <p>
      The tool is currently in a testing phase. Please, be ready to sudden
      breakups and unexpected crashes.
      <span class="text-red-700 font-semibold">
        Use small portions of data with Yandex first!
      </span>
      If you find any bug or have ideas, please report them in any form using
      these links:
    </p>
    <SupportLinks />
  </Panel>
</template>
