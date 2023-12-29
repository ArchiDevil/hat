<script lang="ts">
import {defineComponent} from 'vue'

export default defineComponent({
  emits: ['click'],
})
</script>

<template>
  <button
    @click="($event) => $emit('click', $event)"
    class="py-1 px-2 border rounded border-slate-600 bg-slate-400 text-slate-50 hover:bg-slate-600 transition-colors h-8">
    <slot></slot>
  </button>
</template>
