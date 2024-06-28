<script setup lang="ts">
import {reactive, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {MandeError} from 'mande'

import {login} from '../client/services/AuthService'

import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'

import PageTitle from '../components/PageTitle.vue'
import Checkbox from 'primevue/checkbox'
import {AuthFields} from '../client/schemas/AuthFields'

const fields = reactive<AuthFields>({
  email: '',
  password: '',
  remember: false,
})
const loading = ref(false)
const status = ref<string>()

const route = useRoute()
const router = useRouter()

const authenticate = async () => {
  try {
    loading.value = true
    await login({
      email: fields.email,
      password: fields.password,
      remember: fields.remember,
    })
    await router.push({
      path: (route.query?.redirect as string) || '/',
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
    class="max-w-96 flex flex-col gap-4 border-2 shadow-lg rounded px-4 mt-4 pb-8 mx-auto"
  >
    <PageTitle
      title="Login"
      class="text-center text-color"
    />
    <div class="flex flex-col gap-2">
      <label class="text-color">Email</label>
      <InputText
        v-model="fields.email"
        :disabled="loading"
      />
    </div>
    <div class="flex flex-col gap-2">
      <label class="text-color">Password</label>
      <Password
        v-model="fields.password"
        inputClass="w-full"
        :disabled="loading"
        :feedback="false"
      />
    </div>
    <div class="flex flex-row items-center gap-2">
      <Checkbox
        id="remember"
        v-model="fields.remember"
        :disabled="loading"
        :binary="true"
      />
      <label
        class="text-color"
        @click="fields.remember = !fields.remember"
      >
        Remember me
      </label>
    </div>
    <Button
      label="Login"
      @click="authenticate"
      :disabled="loading"
    />
    <small
      v-if="status"
      class="text-red-700"
    >
      {{ status }}
    </small>
  </div>
</template>
