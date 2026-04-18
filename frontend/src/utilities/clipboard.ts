export const copyToClipboard = async (data: string) => {
  await navigator.clipboard.writeText(data)
}
