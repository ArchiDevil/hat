import {mount} from '@vue/test-utils'
import {describe, it, expect} from 'vitest'
import DocSegment from './DocSegment.vue'

describe('DocSegment', () => {
  it('renders segment number correctly', () => {
    const wrapper = mount(DocSegment, {
      props: {
        rowNumber: 123,
        source: 'Test source',
        target: 'Test target',
      },
    })

    expect(wrapper.text()).toContain('123')
  })

  it('shows repetition dot when repetitionsCount > 1 and editable', () => {
    const wrapper = mount(DocSegment, {
      props: {
        rowNumber: 1,
        source: 'Test source',
        target: 'Test target',
        repetitionsCount: 3,
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).not.toContain('opacity-0')
    expect(dot.attributes('title')).toContain('Repeated 3 times')
  })

  it('does not show repetition dot when repetitionsCount = 1', () => {
    const wrapper = mount(DocSegment, {
      props: {
        rowNumber: 1,
        source: 'Test source',
        target: 'Test target',
        repetitionsCount: 1,
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).toContain('opacity-0')
  })

  it('does not show repetition dot when repetitionsCount is undefined', () => {
    const wrapper = mount(DocSegment, {
      props: {
        rowNumber: 1,
        source: 'Test source',
        target: 'Test target',
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).toContain('opacity-0')
  })
})
