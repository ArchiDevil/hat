<script lang="ts">
import {defineComponent} from 'vue'

import Button from './Button.vue'
import Link from './Link.vue'

export default defineComponent({
  components: {Button, Link},
  props: ['file', 'type'],
  emits: ['delete', 'open'],
})
</script>

<template>
  <div
    class="bg-slate-200 my-1 p-1 border-slate-500 border flex items-baseline"
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
