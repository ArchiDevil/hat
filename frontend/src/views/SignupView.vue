<script setup lang="ts">
import {computed, reactive, ref} from 'vue'
import {MandeError} from 'mande'

import {signup} from '../client/services/AuthService'
import {SignupFields} from '../client/schemas/SignupFields'

import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Panel from 'primevue/panel'

import PageTitle from '../components/PageTitle.vue'

const fields = reactive<SignupFields>({
  email: '',
  username: '',
  registration_token: '',
  password: '',
})

const loading = ref(false)
const touched = ref(false)
const status = ref<string>()
const success = ref(false)

// Email validation regex
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Computed validation
const isEmailValid = computed(() => {
  if (!touched.value) return true
  return fields.email.length > 0 && emailRegex.test(fields.email)
})

const isUsernameValid = computed(() => {
  if (!touched.value) return true
  return fields.username.length >= 3
})

const isPasswordValid = computed(() => {
  if (!touched.value) return true
  return fields.password.length >= 8
})

const isTokenValid = computed(() => {
  if (!touched.value) return true
  return fields.registration_token.length > 0
})

const isFormValid = computed(
  () =>
    isEmailValid.value &&
    isUsernameValid.value &&
    isPasswordValid.value &&
    isTokenValid.value,
)

const register = async () => {
  touched.value = true
  if (!isFormValid.value) return

  try {
    loading.value = true
    await signup({
      email: fields.email,
      username: fields.username,
      registration_token: fields.registration_token,
      password: fields.password,
    })
    success.value = true
  } catch (e) {
    const statusCode = (e as MandeError).response?.status
    if (statusCode == 403) {
      status.value = 'Invalid registration token or user already exists'
    } else if (statusCode == 422) {
      status.value = 'Validation error'
    } else {
      throw e
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="max-w-[432px] flex flex-col gap-4 border-2 border-surface shadow-lg rounded-sm px-4 mt-4 pb-8 mx-auto"
  >
    <PageTitle
      title="Sign Up"
      class="text-center text-color"
    />
    <!-- Success state -->
    <template v-if="success">
      <Message severity="success">
        Your account has been created successfully!
      </Message>
      <div class="text-center">
        <router-link
          :to="{name: 'login'}"
          class="text-primary underline"
        >
          Click here to login
        </router-link>
      </div>
    </template>
    <!-- Registration form -->
    <template v-else>
      <Panel header="Information">
        <p>
          To create an account, you need a registration token. Contact the
          <a
            class="underline"
            href="https://t.me/archidevil"
          >administration</a> to obtain one.
        </p>
        <p class="mt-2">
          <span class="text-red-700">
            There is no way to restore a password right now!
          </span>
          Make sure you've saved it in a safe place.
        </p>
      </Panel>
      <div class="flex flex-col gap-2">
        <label class="text-color">Email</label>
        <InputText
          v-model="fields.email"
          :invalid="!isEmailValid"
          :disabled="loading"
          inputmode="email"
          type="email"
        />
        <Message
          v-if="!isEmailValid"
          severity="error"
          variant="simple"
          size="small"
        >
          Valid email is required
        </Message>
      </div>
      <div class="flex flex-col gap-2">
        <label class="text-color">Username</label>
        <InputText
          v-model="fields.username"
          :invalid="!isUsernameValid"
          :disabled="loading"
        />
        <Message
          v-if="!isUsernameValid"
          severity="error"
          variant="simple"
          size="small"
        >
          Username must be at least 3 characters
        </Message>
      </div>
      <div class="flex flex-col gap-2">
        <label class="text-color">Registration Token</label>
        <InputText
          v-model="fields.registration_token"
          :invalid="!isTokenValid"
          :disabled="loading"
        />
        <Message
          v-if="!isTokenValid"
          severity="error"
          variant="simple"
          size="small"
        >
          Registration token is required
        </Message>
      </div>
      <div class="flex flex-col gap-2">
        <label class="text-color">Password</label>
        <Password
          v-model="fields.password"
          input-class="w-full"
          :invalid="!isPasswordValid"
          :disabled="loading"
          :feedback="false"
        />
        <Message
          v-if="!isPasswordValid"
          severity="error"
          variant="simple"
          size="small"
        >
          Password must be at least 8 characters
        </Message>
      </div>
      <Button
        label="Sign Up"
        :disabled="loading"
        @click="register"
      />
      <small
        v-if="status"
        class="text-red-700"
      >
        {{ status }}
      </small>
      <div class="text-center">
        <router-link
          :to="{name: 'login'}"
          class="text-primary underline"
        >
          Already have an account? Login
        </router-link>
      </div>
    </template>
  </div>
</template>
