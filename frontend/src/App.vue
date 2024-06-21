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
  @apply text-color font-medium font-sans;
}
</style>
