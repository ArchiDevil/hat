import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {getMemories} from '../src/client/services/TmsService'

export const tmMocks = [
  http.get('http://localhost:8000/translation_memory/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getMemories>>([
      {
        id: 42,
        created_by: 12,
        name: 'Some TM',
      },
    ])
  ),
]
