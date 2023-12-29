<script setup lang="ts">
import Button from './Button.vue'
import Link from './Link.vue'

defineEmits(['delete', 'open'])
defineProps(['file', 'type'])
</script>

<template>
  <div
    class="bg-slate-200 my-1 py-1 px-2 border-slate-500 border flex items-baseline"
    style="appearance: button">
    <div class="w-24">#{{ file.id }} {{ file.name }}</div>
    <Link
      :href="`${type}/${file.id}`"
      class="ml-2">
      Open
    </Link>
    <Button
      class="ml-2"
      @click="$emit('delete')">
      Delete
    </Button>
  </div>
</template>
