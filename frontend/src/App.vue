<template>
  <div class="content container">
    <router-view />
  </div>
  <div
    id="modal"
    class="content"
  ></div>
</template>

<style scoped>
.content {
  @apply text-base text-slate-900 font-medium font-sans;
}
</style>
