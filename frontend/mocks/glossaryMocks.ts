import {http, HttpResponse} from 'msw'
import {
  createGlossaryRecord,
  deleteGlossary,
  deleteGlossaryRecord,
  listGlossary,
  listRecords,
  retrieveGlossary,
  updateGlossaryRecord,
} from '../src/client/services/GlossaryService'
import {type AwaitedReturnType} from './utils'
import {defaultUser} from './userMocks'
import {GlossaryRecordCreate} from '../src/client/schemas/GlossaryRecordCreate'
import {GlossaryRecordSchema} from '../src/client/schemas/GlossaryRecordSchema'
import {GlossaryRecordUpdate} from '../src/client/schemas/GlossaryRecordUpdate'
import {GlossaryResponse} from '../src/client/schemas/GlossaryResponse'
import {GlossarySchema} from '../src/client/schemas/GlossarySchema'

const glossaries: GlossaryResponse[] = [
  {
    id: 51,
    name: 'Some glossary',
    created_at: '2024-12-03T12:31:22',
    updated_at: '2024-12-03T16:32:22',
    processing_status: 'done',
    upload_time: '2024-12-03T12:32:05',
    created_by_user: defaultUser,
  },
]

const glossarySegments: GlossaryRecordSchema[] = [
  {
    id: 1,
    glossary_id: 51,
    created_at: '2024-12-03T12:31:22',
    updated_at: '2024-12-03T12:31:22',
    source: 'Some source',
    target: 'Some target',
    comment: 'This is a comment',
    created_by_user: defaultUser,
  },
  {
    id: 2,
    glossary_id: 51,
    created_at: '2024-12-03T12:31:22',
    updated_at: '2024-12-03T12:31:22',
    source: 'Another source',
    target: 'Another target',
    comment: 'Some comment from another segment',
    created_by_user: defaultUser,
  },
]

export const glossaryMocks = [
  http.get('http://localhost:8000/glossary/', () =>
    HttpResponse.json<AwaitedReturnType<typeof listGlossary>>(glossaries)
  ),
  http.get<{id: string}>('http://localhost:8000/glossary/:id', ({params}) => {
    const idx = glossaries.findIndex((g) => g.id === Number(params.id))
    if (idx !== -1) {
      return HttpResponse.json<AwaitedReturnType<typeof retrieveGlossary>>(
        glossaries.at(idx)
      )
    } else {
      return new HttpResponse(null, {status: 404})
    }
  }),
  http.put<{id: string}, GlossarySchema>(
    'http://localhost:8000/glossary/:id',
    async ({request, params}) => {
      const idx = glossaries.findIndex((g) => g.id === Number(params.id))
      if (idx !== -1) {
        const json = await request.json()
        glossaries.at(idx)!.name = json.name
        return HttpResponse.json<AwaitedReturnType<typeof deleteGlossary>>({
          message: 'Ok',
        })
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
  http.delete<{id: string}>(
    'http://localhost:8000/glossary/:id',
    ({params}) => {
      const idx = glossaries.findIndex((g) => g.id === Number(params.id))
      if (idx !== -1) {
        glossaries.splice(idx)
        return HttpResponse.json<AwaitedReturnType<typeof deleteGlossary>>({
          message: 'Ok',
        })
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
  http.get<{id: string}>('http://localhost:8000/glossary/:id/records', () =>
    HttpResponse.json<AwaitedReturnType<typeof listRecords>>(glossarySegments)
  ),
  http.post<{id: string}, GlossaryRecordCreate>(
    'http://localhost:8000/glossary/:id/records',
    async ({request, params}) => {
      const json = await request.json()

      // TODO: ideally it should be stored in a corresponding glossary
      glossarySegments.push({
        id: glossarySegments.at(-1)!.id + 1,
        created_at: '12',
        created_by_user: {
          id: 12,
          username: 'test',
        },
        glossary_id: Number(params.id),
        comment: json.comment,
        source: json.source,
        target: json.target,
        updated_at: '2024-12-03T12:31:22',
      })
      return HttpResponse.json<AwaitedReturnType<typeof createGlossaryRecord>>(
        glossarySegments.at(-1)
      )
    }
  ),
  http.put<{id: string}, GlossaryRecordUpdate>(
    'http://localhost:8000/glossary/records/:id',
    async ({request, params}) => {
      const idx = glossarySegments.findIndex((s) => s.id == Number(params.id))
      if (idx !== -1) {
        const json = await request.json()

        glossarySegments.at(idx)!.source = json.source
        glossarySegments.at(idx)!.target = json.target
        glossarySegments.at(idx)!.comment = json.comment

        return HttpResponse.json<
          AwaitedReturnType<typeof updateGlossaryRecord>
        >({
          id: glossarySegments.at(idx)!.id,
          created_at: '12',
          created_by_user: {
            id: 12,
            username: 'test',
          },
          glossary_id: Number(params.id),
          comment: json.comment,
          source: json.source,
          target: json.target,
          updated_at: '2024-12-03T12:31:22',
        })
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
  http.delete<{id: string}>(
    'http://localhost:8000/glossary/records/:id',
    ({params}) => {
      const idx = glossarySegments.findIndex((s) => s.id == Number(params.id))
      if (idx !== -1) {
        glossarySegments.splice(idx)
        return HttpResponse.json<
          AwaitedReturnType<typeof deleteGlossaryRecord>
        >({
          message: 'Ok',
        })
      } else {
        return new HttpResponse(null, {status: 404})
      }
    }
  ),
]
