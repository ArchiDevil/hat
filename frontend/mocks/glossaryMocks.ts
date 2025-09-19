import {http, HttpResponse} from 'msw'
import {
  listGlossary,
  listRecords,
  retrieveGlossary,
} from '../src/client/services/GlossaryService'
import {type AwaitedReturnType} from './utils'
import {defaultUser} from './userMocks'

export const glossaryMocks = [
  http.get('http://localhost:8000/glossary/', () =>
    HttpResponse.json<AwaitedReturnType<typeof listGlossary>>([
      {
        id: 51,
        name: 'Some glossary',
        created_at: '2024-12-03T12:31:22',
        updated_at: '2024-12-03T16:32:22',
        processing_status: 'done',
        upload_time: '2024-12-03T12:32:05',
        created_by_user: defaultUser,
      },
    ])
  ),
  http.get('http://localhost:8000/glossary/:id', ({params}) =>
    HttpResponse.json<AwaitedReturnType<typeof retrieveGlossary>>({
      id: Number(params.id),
      name: 'Some glossary',
      created_at: '2024-12-03T12:31:22',
      updated_at: '2024-12-03T16:32:22',
      processing_status: 'done',
      upload_time: '2024-12-03T12:32:05',
      created_by_user: defaultUser,
    })
  ),
  http.get('http://localhost:8000/glossary/:id/records', ({params}) =>
    HttpResponse.json<AwaitedReturnType<typeof listRecords>>([
      {
        id: 1,
        glossary_id: Number(params.id),
        created_at: '2024-12-03T12:31:22',
        updated_at: '2024-12-03T12:31:22',
        source: 'Some source',
        target: 'Some target',
        comment: 'This is a comment',
        created_by_user: defaultUser,
      },
      {
        id: 2,
        glossary_id: Number(params.id),
        created_at: '2024-12-03T12:31:22',
        updated_at: '2024-12-03T12:31:22',
        source: 'Another source',
        target: 'Another target',
        comment: 'Some comment from another segment',
        created_by_user: defaultUser,
      },
    ])
  ),
]
