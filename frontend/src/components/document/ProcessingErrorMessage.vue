<script setup lang="ts">
import SupportLinks from '../SupportLinks.vue'
</script>

<template>
  <div class="flex flex-col gap-2">
    <p class="text-red-700">
      Error while processing the document. We still provide you the document
      content. It might be processed partially.
    </p>
    <p>If this problem persists, use one of these links to report an issue:</p>
    <SupportLinks />
  </div>
</template>
