import {http, HttpResponse} from 'msw'
import {faker} from '@faker-js/faker'

import {AwaitedReturnType} from './utils'
import {
  getDoc,
  getDocRecords,
  getDocs,
  getRecordGlossaryRecords,
  getRecordSubstitutions,
  updateDocRecord,
} from '../src/client/services/DocumentService'
import {DocumentStatus} from '../src/client/schemas/DocumentStatus'
import {DocumentRecordUpdate} from '../src/client/schemas/DocumentRecordUpdate'

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
    approved: false,
    source:
      'The moment the Cynidiceans pried the horn from the monolith, their city was doomed.',
    target:
      'В тот момент, когда кинидийцы извлекли рог из монолита, их город был обречен.',
    repetitions_count: 1,
  },
  {
    id: 10002,
    approved: true,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 2,
  },
]

const recordsData = {
  page: 0,
  total_records: segments.length,
  records: segments,
}

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
      return new HttpResponse(null, {status: 404})
    }
  }),
  http.get<{id: string}>(
    'http://localhost:8000/document/:id/records',
    ({params}) => {
      const doc = docs.find((doc) => doc.id === Number(params.id))
      if (doc !== undefined) {
        return HttpResponse.json<AwaitedReturnType<typeof getDocRecords>>(
          recordsData
        )
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
  http.put<{id: string}, DocumentRecordUpdate>(
    'http://localhost:8000/document/record/:id',
    async ({params, request}) => {
      const record = segments.find((s) => s.id === Number(params.id))
      if (!record) {
        return new HttpResponse(null, {status: 404})
      }
      const req = await request.json()
      if (req.approved) record.approved = req.approved
      record.target = req.target
      return HttpResponse.json<AwaitedReturnType<typeof updateDocRecord>>({
        approved: false,
        id: record.id,
        source: record.source,
        target: record.target,
      })
    }
  ),
  http.get<{id: string; segmentId: string}>(
    'http://localhost:8000/document/:id/records/:segmentId/substitutions',
    ({params}) => {
      const doc = docs.find((doc) => doc.id === Number(params.id))
      if (doc !== undefined) {
        return HttpResponse.json<
          AwaitedReturnType<typeof getRecordSubstitutions>
        >([
          {
            source: 'Substitution test',
            target: 'Тест подстановки',
            similarity: 0.94,
          },
          {
            source: 'Something else',
            target: 'Что-то еще',
            similarity: 0.84,
          },
        ])
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
  http.get<{id: string; segmentId: string}>(
    'http://localhost:8000/document/:id/records/:segmentId/glossary_records',
    ({params}) => {
      const doc = docs.find((doc) => doc.id === Number(params.id))
      if (doc !== undefined) {
        return HttpResponse.json<
          AwaitedReturnType<typeof getRecordGlossaryRecords>
        >([
          {
            id: 1,
            source: 'Test',
            target: 'Тест',
            glossary_id: 2,
            created_at: faker.date.recent().toISOString().split('.')[0],
            updated_at: faker.date.recent().toISOString().split('.')[0],
            comment: '',
            created_by_user: {
              id: 42,
              username: 'User',
            },
          },
          {
            id: 2,
            source: 'Another test',
            target: 'Другой тест',
            glossary_id: 2,
            created_at: faker.date.recent().toISOString().split('.')[0],
            updated_at: faker.date.recent().toISOString().split('.')[0],
            comment: '',
            created_by_user: {
              id: 42,
              username: 'User',
            },
          },
        ])
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
]
