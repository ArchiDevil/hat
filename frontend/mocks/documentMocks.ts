import {http, HttpResponse} from 'msw'
import {faker, fakerRU} from '@faker-js/faker'

import {glossaries} from './glossaryMocks'
import {AwaitedReturnType} from './utils'
import {
  getDoc,
  getDocRecords,
  getGlossaries,
} from '../src/client/services/DocumentService'
import {
  getComments,
  getRecordGlossaryRecords,
  getRecordSubstitutions,
  getSegmentHistory,
  updateDocRecord,
} from '../src/client/services/RecordsService'
import {DocumentStatus} from '../src/client/schemas/DocumentStatus'
import {DocumentRecordUpdate} from '../src/client/schemas/DocumentRecordUpdate'
import {CommentResponse} from '../src/client/schemas/CommentResponse'
import {DocumentRecord} from '../src/client/schemas/DocumentRecord'
import {DocumentWithRecordsCount} from '../src/client/schemas/DocumentWithRecordsCount'

const segmentComments: CommentResponse[] = [
  {
    id: 1,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10001,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 2,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 3,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 4,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 5,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 6,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 7,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 8,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 9,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 10,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 11,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 12,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 13,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 14,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 15,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
  {
    id: 16,
    created_by_user: {
      id: 42,
      username: faker.internet.email(),
    },
    record_id: 10002,
    text: fakerRU.commerce.productDescription(),
    updated_at: faker.date.recent().toISOString().split('.')[0],
  },
]

const segments: DocumentRecord[] = [
  {
    id: 10000,
    approved: false,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 2,
    has_comments: false,
  },
  {
    id: 10001,
    approved: false,
    source:
      'The moment the Cynidiceans pried the horn from the monolith, their city was doomed.',
    target:
      'В тот момент, когда кинидийцы извлекли рог из монолита, их город был обречен.',
    repetitions_count: 1,
    has_comments: true,
  },
  {
    id: 10002,
    approved: true,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 2,
    has_comments: true,
  },
  {
    id: 10003,
    approved: true,
    source: 'Adventure Hooks',
    target: 'Зацепки приключения',
    repetitions_count: 3,
    has_comments: false,
  },
]

const recordsData = {
  page: 0,
  total_records: segments.length,
  records: segments,
}

const docs: DocumentWithRecordsCount[] = [
  {
    id: 1,
    created_by: 12,
    total_records_count: segments.length,
    approved_records_count: segments.filter(({approved}) => approved).length,
    total_word_count: 20,
    approved_word_count: 4,
    name: 'Some document',
    status: 'done' as DocumentStatus,
    type: 'XLIFF',
  },
]

export const documentMocks = [
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
  http.get<{id: string}>(
    'http://localhost:8000/document/:id/glossaries',
    ({params}) => {
      const doc = docs.find((doc) => doc.id === Number(params.id))
      if (doc !== undefined) {
        return HttpResponse.json<AwaitedReturnType<typeof getGlossaries>>([
          {
            document_id: doc.id,
            glossary: glossaries[0],
          },
        ])
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
  http.get<{segmentId: string}>(
    'http://localhost:8000/document/records/:segmentId/comments',
    ({params}) => {
      const output: AwaitedReturnType<typeof getComments> = []
      for (const comm of segmentComments) {
        if (comm.record_id == Number(params.segmentId)) {
          output.push(comm)
        }
      }
      return HttpResponse.json(output)
    }
  ),
  http.get<{segmentId: string}>(
    'http://localhost:8000/document/records/:segmentId/history',
    () => {
      return HttpResponse.json<AwaitedReturnType<typeof getSegmentHistory>>({
        history: [
          {
            id: 2,
            author: {
              id: 42,
              username: 'User',
            },
            change_type: 'manual_edit',
            diff: JSON.stringify({
              ops: [
                ['equal', 0, 4],
                ['delete', 4, 12],
                ['equal', 12, 34],
                ['insert', 34, 34, ' этими'],
                ['equal', 34, 73],
                ['replace', 73, 82, 'указа'],
                ['equal', 82, 117],
              ],
              old_len: 50,
            }),
            timestamp: faker.date.recent().toISOString().split('.')[0],
          },
          {
            id: 1,
            author: {
              id: 42,
              username: 'User',
            },
            change_type: 'initial_import',
            diff: JSON.stringify({
              ops: [
                [
                  'insert',
                  0,
                  0,
                  'Семь из этих предысторий связаны с фракциями, описанными в главе 6 — они перечислены в таблице «Предыстории фракций».',
                ],
              ],
              old_len: 0,
            }),
            timestamp: faker.date.past().toISOString().split('.')[0],
          },
        ],
      })
    }
  ),
]
