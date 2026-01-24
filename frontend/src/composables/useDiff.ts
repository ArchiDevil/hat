export type DiffOp = (string | number)[]

export interface DiffData {
  ops: DiffOp[]
  old_len: number
}

export interface DiffPart {
  text: string
  type: 'equal' | 'added' | 'removed'
}

/**
 * Apply diff operations to a text string and return the new text
 * Operations are processed in forward order using string manipulation
 */
export const applyDiffOps = (
  text: string,
  ops: DiffOp[]
): {newText: string; diffParts: DiffPart[]} => {
  let result = ''
  const diffParts: DiffPart[] = []

  // Process operations in forward order
  for (const op of ops) {
    const tag = op[0] as 'replace' | 'delete' | 'equal' | 'insert'
    const i1 = op[1] as number
    const i2 = op[2] as number
    const newSegment = op.length > 2 ? (op[3] as string) : undefined

    if (tag === 'equal') {
      // Copy as is
      result += text.substring(i1, i2)
      diffParts.push({text: text.substring(i1, i2), type: 'equal'})
    } else if (tag === 'replace') {
      result += newSegment
      diffParts.push({text: text.substring(i1, i2), type: 'removed'})
      diffParts.push({text: newSegment ?? '', type: 'added'})
    } else if (tag === 'delete') {
      // Skipped, do not copy
      diffParts.push({text: text.substring(i1, i2), type: 'removed'})
    } else if (tag === 'insert') {
      result += newSegment
      diffParts.push({text: newSegment ?? '', type: 'added'})
    }
  }

  return {newText: result, diffParts}
}
