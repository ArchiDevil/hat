import {mount} from '@vue/test-utils'
import {describe, it, expect} from 'vitest'
import DocSegment from './DocSegment.vue'

describe('DocSegment', () => {
  it('renders segment ID correctly', () => {
    const wrapper = mount(DocSegment, {
      props: {
        id: 123,
        source: 'Test source',
        target: 'Test target',
        editable: true,
      },
    })

    expect(wrapper.text()).toContain('123')
  })

  it('shows repetition dot when repetitionsCount > 1 and editable', () => {
    const wrapper = mount(DocSegment, {
      props: {
        id: 123,
        source: 'Test source',
        target: 'Test target',
        editable: true,
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
        id: 123,
        source: 'Test source',
        target: 'Test target',
        editable: true,
        repetitionsCount: 1,
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).toContain('opacity-0')
  })

  it('does not show repetition dot when not editable', () => {
    const wrapper = mount(DocSegment, {
      props: {
        id: 123,
        source: 'Test source',
        target: 'Test target',
        editable: false,
        repetitionsCount: 3,
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).toContain('opacity-0')
  })

  it('does not show repetition dot when repetitionsCount is undefined', () => {
    const wrapper = mount(DocSegment, {
      props: {
        id: 123,
        source: 'Test source',
        target: 'Test target',
        editable: true,
      },
    })

    const dot = wrapper.find('.pi')
    expect(dot.classes()).toContain('opacity-0')
  })
})
