import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {defaults} from 'mande'

import PrimeVue from 'primevue/config'
import {definePreset} from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import App from './App.vue'
import {getRouter} from './router'

// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
const themePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{sky.50}',
      100: '{sky.100}',
      200: '{sky.200}',
      300: '{sky.300}',
      400: '{sky.400}',
      500: '{sky.500}',
      600: '{sky.600}',
      700: '{sky.700}',
      800: '{sky.800}',
      900: '{sky.900}',
      950: '{sky.950}',
    },
  },
})

const pinia = createPinia()

if (import.meta.env.DEV) {
  // to test it locally
  defaults.credentials = 'include'
}

// eslint-disable-next-line @typescript-eslint/no-unsafe-argument
const app = createApp(App)
app.use(pinia)
app.use(PrimeVue, {
  theme: {
    preset: themePreset as unknown,
    options: {
      darkModeSelector: '',
      cssLayer: {
        name: 'primevue',
        order: 'tailwind-base, primevue, tailwind-utilities',
      },
    },
  },
})

app.use(getRouter())
app.config.errorHandler = (err, instance, info) => {
  // TODO: add some kind of a monitoring system like sentry
  console.log('Error: ', err, '- ', info)
  console.log(instance)
}
app.mount('#app')
