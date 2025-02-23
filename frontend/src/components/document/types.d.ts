interface Substitution {
  source: string
  target: string
}

export interface MemorySubstitution extends Substitution {
  type: 'memory'
  similarity: number // ranging from 0.0 to 1.0
}

export interface GlossarySubstitution extends Substitution {
  type: 'glossary'
  comment?: string
  parentName: string
}
