import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {
  getDoc,
  getDocRecords,
  getDocs,
} from '../src/client/services/DocumentService'
import {DocumentStatus} from '../src/client/schemas/DocumentStatus'

const segments = [
  {
    id: 10000,
    approved: false,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 2,
  },
  {
    id: 10001,
    approved: true,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 2,
  },
  {
    id: 10002,
    approved: false,
    source:
      'The moment the Cynidiceans pried the horn from the monolith, their city was doomed.',
    target:
      'В тот момент, когда кинидийцы извлекли рог из монолита, их город был обречен.',
    repetitions_count: 1,
  },
]

const docs = [
  {
    id: 1,
    created_by: 12,
    records_count: segments.length,
    approved_records_count: segments.filter(({approved}) => approved).length,
    name: 'Some document',
    status: 'done' as DocumentStatus,
    type: 'XLIFF',
  },
]

export const documentMocks = [
  http.get('http://localhost:8000/document/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getDocs>>(docs)
  ),
  http.get<{id: string}>('http://localhost:8000/document/:id', ({params}) => {
    const doc = docs.find((doc) => doc.id === Number(params.id))
    if (doc !== undefined) {
      return HttpResponse.json<AwaitedReturnType<typeof getDoc>>(doc)
    } else {
      new HttpResponse(null, {status: 404})
    }
  }),
  http.get<{id: string}>(
    'http://localhost:8000/document/:id/records',
    ({params}) => {
      const doc = docs.find((doc) => doc.id === Number(params.id))
      if (doc !== undefined) {
        return HttpResponse.json<AwaitedReturnType<typeof getDocRecords>>(
          segments
        )
      } else {
        new HttpResponse(null, {status: 404})
      }
    }
  ),
]
