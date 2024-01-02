<script setup lang="ts">
import Button from './Button.vue'
import RoutingLink from './RoutingLink.vue'

defineEmits(['delete'])
defineProps(['file', 'type', 'busy'])
</script>

<template>
  <div
    class="bg-slate-200 my-1 py-1 px-2 border-slate-500 border flex items-baseline">
    <div class="w-48 text-ellipsis whitespace-nowrap overflow-hidden">
      #{{ file.id }} {{ file.name }}
    </div>
    <RoutingLink
      :href="`${type}/${file.id}`"
      class="ml-2"
      :disabled="busy">
      Open
    </RoutingLink>
    <Button
      class="ml-2"
      @click="$emit('delete')"
      :disabled="busy">
      Delete
    </Button>
    <span
      class="ml-2"
      v-if="busy">
      Busy...
    </span>
  </div>
</template>
