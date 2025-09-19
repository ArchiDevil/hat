export type AwaitedReturnType<F extends (...args: never) => unknown> = Awaited<
  ReturnType<F>
>
