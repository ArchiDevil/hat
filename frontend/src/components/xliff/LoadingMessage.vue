<script setup lang="ts">
import SupportLinks from '../SupportLinks.vue'
</script>

<template>
  <div class="flex flex-col gap-2">
    <p>The document is being processed right now. This should not take long.</p>
    <p>
      If the file is processed too long (it not should take more than 5-10
      minutes), use one of these links to report an issue:
    </p>
    <SupportLinks />
  </div>
</template>
