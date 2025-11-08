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
  let timeout: ReturnType<typeof setTimeout> | null

  return (...args: Args): void => {
    if (timeout !== null) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}
