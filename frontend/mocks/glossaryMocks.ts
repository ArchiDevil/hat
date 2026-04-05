import {http, HttpResponse} from 'msw'
import {faker} from '@faker-js/faker'
import {fakerRU} from '@faker-js/faker'

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

const genSegments = (
  startId: number,
  glossaryId: number,
  count: number
): GlossaryRecordSchema[] => {
  return new Array(count).fill(null).map((_, idx) => {
    return {
      id: startId + idx,
      glossary_id: glossaryId,
      created_at: faker.date.recent().toISOString().split('.')[0],
      updated_at: faker.date.recent().toISOString().split('.')[0],
      source: faker.commerce.productName(),
      target: fakerRU.commerce.productName(),
      comment: fakerRU.commerce.productDescription(),
      created_by_user: defaultUser,
    }
  })
}

export const glossaries: (GlossaryResponse & {
  segments: GlossaryRecordSchema[]
})[] = [
  {
    id: 51,
    name: 'Some glossary',
    created_at: faker.date.recent().toISOString().split('.')[0],
    updated_at: faker.date.recent().toISOString().split('.')[0],
    processing_status: 'done',
    upload_time: faker.date.recent().toISOString().split('.')[0],
    created_by_user: defaultUser,
    segments: genSegments(1, 51, 125),
    records_count: 125,
  },
  {
    id: 52,
    name: 'Such a long long long long long name of the glossary to the its truncation',
    created_at: faker.date.recent().toISOString().split('.')[0],
    updated_at: faker.date.recent().toISOString().split('.')[0],
    processing_status: 'done',
    upload_time: faker.date.recent().toISOString().split('.')[0],
    created_by_user: defaultUser,
    segments: genSegments(1000, 52, 280),
    records_count: 280,
  },
]

export const glossaryMocks = [
  http.get('http://localhost:8000/glossary/', () =>
    HttpResponse.json<AwaitedReturnType<typeof listGlossary>>(glossaries)
  ),
  http.get<{id: string}>('http://localhost:8000/glossary/:id', ({params}) => {
    const idx = glossaries.findIndex((g) => g.id === Number(params.id))
    if (idx === -1) {
      return new HttpResponse(null, {status: 404})
    }

    return HttpResponse.json<AwaitedReturnType<typeof retrieveGlossary>>(
      glossaries.at(idx)
    )
  }),
  http.put<{id: string}, GlossarySchema>(
    'http://localhost:8000/glossary/:id',
    async ({request, params}) => {
      const idx = glossaries.findIndex((g) => g.id === Number(params.id))
      if (idx === -1) {
        return new HttpResponse(null, {status: 404})
      }

      const json = await request.json()
      glossaries.at(idx)!.name = json.name
      return HttpResponse.json<AwaitedReturnType<typeof deleteGlossary>>({
        message: 'Ok',
      })
    }
  ),
  http.delete<{id: string}>(
    'http://localhost:8000/glossary/:id',
    ({params}) => {
      const idx = glossaries.findIndex((g) => g.id === Number(params.id))
      if (idx === -1) {
        return new HttpResponse(null, {status: 404})
      }

      glossaries.splice(idx)
      return HttpResponse.json<AwaitedReturnType<typeof deleteGlossary>>({
        message: 'Ok',
      })
    }
  ),
  http.get<{id: string}>(
    'http://localhost:8000/glossary/:id/records',
    ({request, params}) => {
      const searchParams = new URL(request.url).searchParams
      const page = Number(searchParams.get('page') ?? '0')
      let search = searchParams.get('search')
      if (search == 'null' || search == 'undefined') search = ''

      const glossary = glossaries.find((g) => g.id == parseInt(params.id))
      if (!glossary) {
        return new HttpResponse(null, {status: 404})
      }

      const records = glossary.segments
        .filter(
          (seg) =>
            seg.source.includes(search ?? '') ||
            seg.target.includes(search ?? '')
        )
        .slice(page * 100, page * 100 + 100)

      return HttpResponse.json<AwaitedReturnType<typeof listRecords>>({
        records,
        total_rows: search == '' ? glossary.segments.length : records.length,
      })
    }
  ),
  http.post<{id: string}, GlossaryRecordCreate>(
    'http://localhost:8000/glossary/:id/records',
    async ({request, params}) => {
      const json = await request.json()

      const glossary = glossaries.find((g) => g.id == parseInt(params.id))
      if (!glossary) {
        return new HttpResponse(null, {status: 404})
      }

      glossary.segments.push({
        id: glossary.segments.at(-1)!.id + 1,
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
        glossary.segments.at(-1)
      )
    }
  ),
  http.put<{id: string}, GlossaryRecordUpdate>(
    'http://localhost:8000/glossary/records/:id',
    async ({request, params}) => {
      const id = parseInt(params.id)
      const json = await request.json()

      let found = false
      for (const glossary of glossaries) {
        const idx = glossary.segments.findIndex((s) => s.id == id)
        if (idx !== -1) {
          glossary.segments[idx].source = json.source
          glossary.segments[idx].target = json.target
          glossary.segments[idx].comment = json.comment
          found = true
        }
      }

      if (!found) {
        return new HttpResponse(null, {status: 404})
      }

      return HttpResponse.json<AwaitedReturnType<typeof updateGlossaryRecord>>({
        id: id,
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
    }
  ),
  http.delete<{id: string}>(
    'http://localhost:8000/glossary/records/:id',
    ({params}) => {
      const id = parseInt(params.id)

      let found = false
      for (const glossary of glossaries) {
        const idx = glossary.segments.findIndex((s) => s.id == id)
        if (idx !== -1) {
          glossary.segments.splice(idx)
          found = true
        }
      }

      if (!found) {
        return new HttpResponse(null, {status: 404})
      }

      return HttpResponse.json<AwaitedReturnType<typeof deleteGlossaryRecord>>({
        message: 'Ok',
      })
    }
  ),
]
