import {beforeEach, expect, it, vi} from 'vitest'
import {flushPromises, mount} from '@vue/test-utils'

import Index from './Index.vue'

beforeEach(() => {
  // TODO: update to use apiAccessor
  vi.restoreAllMocks()
  vi.unmock('mande')
})

it('mounts', async () => {
  vi.mock('mande', async (importOriginal) => {
    const original = await importOriginal<typeof import('mande')>()
    return {
      ...original,
      mande: () => {
        return {
          get: async () => {
            return [
              {id: 1, name: 'test1'},
              {id: 2, name: 'test2'},
            ]
          },
        }
      },
    }
  })
  const wrapper = mount(Index)
  await flushPromises()

  expect(wrapper.text()).toContain('test1')
  expect(wrapper.text()).toContain('test2')
})
