import {createApp} from 'vue'
import {createPinia} from 'pinia'

import PrimeVue from 'primevue/config'
import {definePreset} from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import App from './App.vue'
import {getRouter} from './router'

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

const startApp = () => {
  const pinia = createPinia()
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
}

if (import.meta.env.PROD) {
  startApp()
}

// Dev server things

import {defaults} from 'mande'
import {setupWorker} from 'msw/browser'

if (import.meta.env.DEV) {
  defaults.credentials = 'include'

  const mocksImport = () => import('../mocks/mocks')
  mocksImport()
    .then((imp) => {
      setupWorker(...imp.mocks)
        .start()
        .then(() => {
          startApp()
        })
        .catch((e) => {
          console.log('MSW init failed', e)
        })
    })
    .catch(() => {
      console.log('Failed to load mocks')
    })
}
