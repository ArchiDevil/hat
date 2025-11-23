import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {getMemories, getMemory} from '../src/client/services/TmsService'
import {TranslationMemoryWithRecordsCount} from '../src/client/schemas/TranslationMemoryWithRecordsCount'

const tms: TranslationMemoryWithRecordsCount[] = [
  {
    id: 42,
    created_by: 12,
    name: 'Some TM',
    records_count: 5,
  },
]

export const tmMocks = [
  http.get('http://localhost:8000/translation_memory/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getMemories>>(tms)
  ),
  http.get<{id: string}>(
    'http://localhost:8000/translation_memory/:id',
    ({params}) => {
      const id = Number(params.id)
      const tm = tms.find((t) => t.id == id)
      if (tm) {
        return HttpResponse.json<AwaitedReturnType<typeof getMemory>>(tm)
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
]
