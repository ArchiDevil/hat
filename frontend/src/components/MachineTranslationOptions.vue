<script setup lang="ts">
import {YandexTranslatorSettings} from '../client/schemas/YandexTranslatorSettings'
import {LlmTranslatorSettings} from '../client/schemas/LlmTranslatorSettings'

import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

export type MtType = 'yandex' | 'llm'

export interface Model {
  enabled: boolean
  type: MtType
  yandexSettings: YandexTranslatorSettings
  llmSettings: LlmTranslatorSettings
}

const model = defineModel<Model>({required: true})
const machineTranslationTypes = [
  {name: 'Yandex Translator', value: 'yandex' as MtType},
  {name: 'LLM Translator', value: 'llm' as MtType},
]
</script>

<template>
  <div>
    <div class="flex items-center">
      <Checkbox
        id="umt"
        v-model="model.enabled"
        :binary="true"
      />
      <label
        for="umt"
        class="ml-2"
        @click="model.enabled = !model.enabled"
      >
        Use machine translation
      </label>
    </div>
    <div
      v-if="model.enabled"
      class="flex flex-col gap-2 max-w-[32rem]"
    >
      <div class="flex flex-col gap-2 mb-4 max-w-96 mt-3">
        <label>Machine translation type:</label>
        <Select
          v-model="model.type"
          :options="machineTranslationTypes"
          option-label="name"
          option-value="value"
          placeholder="Select translation type"
        />
      </div>

      <!-- Yandex Translator Options -->
      <div
        v-if="model.type === 'yandex'"
        class="flex flex-col gap-2"
      >
        <p class="font-semibold">
          Yandex translator options
          <a
            href="https://yandex.cloud/ru/docs/translate/api-ref/authentication"
            class="font-normal underline decoration-1 hover:decoration-2"
            target="_blank"
          >
            (Where to get credentials?)
          </a>
        </p>
        <div class="flex items-center flex-row gap-2">
          <label
            for="fid"
            class="flex-grow"
          >
            Folder ID
          </label>
          <InputText
            id="fid"
            v-model="model.yandexSettings.folder_id"
            class="w-96"
          />
        </div>
        <div class="flex items-center flex-row gap-2">
          <label
            for="oauth"
            class="flex-grow"
          >
            OAuth token
          </label>
          <InputText
            id="oauth"
            v-model="model.yandexSettings.oauth_token"
            class="w-96"
          />
        </div>
      </div>

      <!-- LLM Translator Options -->
      <div
        v-if="model.type === 'llm'"
        class="flex flex-col gap-2"
      >
        <p class="font-semibold">
          LLM translator options
        </p>
        <div class="flex items-center flex-row gap-2">
          <label
            for="apiKey"
            class="flex-grow"
          >
            API Key
          </label>
          <InputText
            id="apiKey"
            v-model="model.llmSettings.api_key"
            class="w-96"
          />
        </div>
      </div>
    </div>
  </div>
</template>
