type CallbackFunction = (...args: unknown[]) => void

export const debounce = (
  func: CallbackFunction,
  wait: number
): CallbackFunction => {
  let timeout: ReturnType<typeof setTimeout> | null

  return (...args: unknown[]): void => {
    if (timeout !== null) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func.apply(this, args)
    }, wait)
  }
}
