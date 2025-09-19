import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {getDocs} from '../src/client/services/DocumentService'

export const documentMocks = [
  http.get('http://localhost:8000/document/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getDocs>>([
      {
        id: 1,
        created_by: 12,
        records_count: 450,
        approved_records_count: 247,
        name: 'Some document',
        status: 'done',
        type: 'XLIFF',
      },
    ])
  ),
]
