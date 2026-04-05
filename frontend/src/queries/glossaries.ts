import {defineQuery, useQuery} from '@pinia/colada'
import {listGlossary} from '../client/services/GlossaryService'

export const GLOSSARY_KEYS = {
  root: ['glossaries'] as const,
  byId: (glossaryId: number) => [...GLOSSARY_KEYS.root, glossaryId] as const,
  recordsById: (glossaryId: number) =>
    [...GLOSSARY_KEYS.byId(glossaryId), 'records'] as const,
  recordsByIdPaged: (glossaryId: number, page: number) =>
    [...GLOSSARY_KEYS.recordsById(glossaryId), page] as const,
  recordsWithSearch: (glossaryId: number, page: number, search: string) =>
    [
      ...GLOSSARY_KEYS.recordsByIdPaged(glossaryId, page),
      'search',
      search,
    ] as const,
}

export const useGlossaries = defineQuery(() => {
  const data = useQuery({
    key: () => GLOSSARY_KEYS.root,
    query: async () => {
      return await listGlossary()
    },
    placeholderData: (prevData) => prevData,
  })
  return data
})
