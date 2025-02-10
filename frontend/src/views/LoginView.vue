<script setup lang="ts">
import {reactive, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {MandeError} from 'mande'

import {login} from '../client/services/AuthService'
import {AuthFields} from '../client/schemas/AuthFields'

import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Panel from 'primevue/panel'

import PageTitle from '../components/PageTitle.vue'

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
    const statusCode = (e as MandeError).response?.status
    if (statusCode == 401 || statusCode == 402) {
      status.value = 'Invalid email or password'
    } else if (statusCode == 503) {
      status.value = 'Service unavailable, try again later.'
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
    class="max-w-96 flex flex-col gap-4 border-2 shadow-lg rounded px-4 mt-4 pb-8 mx-auto"
  >
    <PageTitle
      title="Login"
      class="text-center text-color"
    />
    <Panel header="Information">
      <p>
        Currently, the access to the website is limited. To apply for access,
        write a message to the
        <a
          class="underline"
          href="https://t.me/archidevil"
        >administration</a>. It will be opened to the public in the future.
      </p>
      <p class="mt-2">
        <span class="text-red-700">
          There is no way to restore a password right now!
        </span>
        Make sure you've saved it in a safe place after you've got an access. If
        you lost it, contact the
        <a
          class="underline"
          href="https://t.me/archidevil"
        >administration</a>.
      </p>
    </Panel>
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
        input-class="w-full"
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
      :disabled="loading"
      @click="authenticate"
    />
    <small
      v-if="status"
      class="text-red-700"
    >
      {{ status }}
    </small>
  </div>
</template>
