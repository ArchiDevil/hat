<script setup lang="ts">
import {TmxFileRecord} from '../client/schemas/TmxFileRecord'
import {XliffFileRecord} from '../client/schemas/XliffFileRecord'

defineProps<{
  record: TmxFileRecord | XliffFileRecord
}>()
</script>

<template>
  <div class="grid grid-cols-2 gap-2 mb-1">
    <p class="border-2 rounded p-2">
      {{ record.source }}
    </p>
    <p class="border-2 rounded p-2">
      {{ record.target }}
    </p>
  </div>
</template>
