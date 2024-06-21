<script setup lang="ts">
import {ref} from 'vue'
import {MandeError} from 'mande'
import {useRouter} from 'vue-router'

import {login} from '../client/services/AuthService'

import AppButton from '../components/AppButton.vue'
import LabeledTextInput from '../components/LabeledTextInput.vue'
import PageTitle from '../components/PageTitle.vue'

const email = ref('')
const password = ref('')
const loading = ref(false)
const status = ref<string>()
const router = useRouter()

const authenticate = async () => {
  try {
    loading.value = true
    await login({
      email: email.value,
      password: password.value,
    })
    const result = await router.replace({
      path: '/',
    })
  } catch (e) {
    const err = e as MandeError
    console.error(err.message)
    const statusCode = err.response?.status
    if (statusCode == 401) {
      status.value = 'Invalid email or password'
    } else if (statusCode == 422) {
      status.value = 'Invalid email or password'
    } else if (statusCode == 503) {
      status.value = 'Service unavailable, try again later.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="max-w-96 flex flex-col gap-2 border-2 shadow-lg rounded px-4 mt-4 pb-8 mx-auto"
  >
    <PageTitle title="Login" />
    <LabeledTextInput
      title="Email"
      v-model="email"
      :disabled="loading"
    />
    <LabeledTextInput
      title="Password"
      v-model="password"
      password
      :disabled="loading"
    />
    <AppButton
      @click="authenticate"
      :disabled="loading"
    >
      Login
    </AppButton>
    <p
      v-if="status"
      class="text-red-700 text-sm"
    >
      {{ status }}
    </p>
  </div>
</template>
