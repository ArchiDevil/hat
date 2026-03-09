import {defineQuery, useQuery} from '@pinia/colada'
import {getMemories} from '../client/services/TmsService'

export const TM_KEYS = {
  root: ['memories'] as const,
}

export const useTranslationMemories = defineQuery(() => {
  const data = useQuery({
    key: () => TM_KEYS.root,
    query: async () => {
      return await getMemories()
    },
    placeholderData: <T>(prevData: T) => prevData,
  })
  return data
})
