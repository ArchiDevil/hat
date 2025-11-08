import {it, expect, vi, beforeEach, describe, afterEach} from 'vitest'
import {debounce} from './utils'

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should delay function execution', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce(mockFn, 1000)

    debouncedFn()
    expect(mockFn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1000)
    expect(mockFn).toHaveBeenCalledTimes(1)
  })

  it('should preserve parameter types', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce((value: string) => {
      mockFn(value)
    }, 100)

    debouncedFn('test')
    vi.advanceTimersByTime(100)

    expect(mockFn).toHaveBeenCalledWith('test')
  })

  it('should handle multiple parameters', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce((a: number, b: string, c: boolean) => {
      mockFn(a, b, c)
    }, 100)

    debouncedFn(42, 'hello', true)
    vi.advanceTimersByTime(100)

    expect(mockFn).toHaveBeenCalledWith(42, 'hello', true)
  })

  it('should cancel previous calls when called multiple times', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce(mockFn, 100)

    debouncedFn('first')
    debouncedFn('second')
    debouncedFn('third')

    vi.advanceTimersByTime(100)

    expect(mockFn).toHaveBeenCalledTimes(1)
    expect(mockFn).toHaveBeenCalledWith('third')
  })

  it('should handle optional string parameters', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce((value: string | undefined) => {
      if (value !== undefined) {
        mockFn(value)
      }
    }, 100)

    debouncedFn('test')
    vi.advanceTimersByTime(100)

    expect(mockFn).toHaveBeenCalledWith('test')
  })

  it('should not call function with undefined when handled properly', () => {
    const mockFn = vi.fn()
    const debouncedFn = debounce((value: string | undefined) => {
      if (value !== undefined) {
        mockFn(value)
      }
    }, 100)

    debouncedFn(undefined)
    vi.advanceTimersByTime(100)

    expect(mockFn).not.toHaveBeenCalled()
  })
})
