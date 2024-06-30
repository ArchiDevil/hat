import {it, expect} from 'vitest'
import {createPinia} from 'pinia'

import {TmxFile} from '../client/schemas/TmxFile'
import {useTmxStore} from './tmx'

it('filters selected ids', async () => {
  const store = useTmxStore(createPinia())
  store.selectedTmxFiles = [
    {
      id: 123,
      name: 'abc',
      created_by: 1,
    },
    {
      id: 456,
      name: 'def',
      created_by: 2,
    },
  ]
  expect(store.selectedIds).toEqual([123, 456])
})
