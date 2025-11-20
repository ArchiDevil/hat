export const cleanableDebounce = <Args extends unknown[]>(
  func: (...args: Args) => void,
  wait: number
) => {
  let timeout: ReturnType<typeof setTimeout> | null

  const clear = () => {
    if (timeout !== null) {
      clearTimeout(timeout)
    }
  }

  return {
    func: (...args: Args): void => {
      clear()
      timeout = setTimeout(() => {
        func(...args)
      }, wait)
    },
    clear,
  }
}

/**
 * Creates a debounced version of a function that delays execution until after the specified wait time.
 * The debounced function preserves the original function's parameter types.
 *
 * @template Args - The tuple type of function arguments
 * @param func - The function to debounce
 * @param wait - The delay in milliseconds
 * @returns A debounced version of the function with the same parameter types
 */
export const debounce = <Args extends unknown[]>(
  func: (...args: Args) => void,
  wait: number
): ((...args: Args) => void) => {
  return cleanableDebounce(func, wait).func
}
