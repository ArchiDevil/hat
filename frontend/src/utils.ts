type CallbackFunction = (...args: any[]) => void

export const debounce = (
  func: CallbackFunction,
  wait: number
): CallbackFunction => {
  let timeout: ReturnType<typeof setTimeout> | null

  return (...args: any[]): void => {
    const context = this

    if (timeout !== null) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func.apply(context, args)
    }, wait)
  }
}
