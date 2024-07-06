import {writeGeneratedContent} from './utils'

export const genDefaults = (output: string, apiPrefix: string): void => {
  const content = [
    `export const getApiBase = () => {`,
    `  if (import.meta.env.DEV) {`,
    `    return 'http://localhost:8000'`,
    `  } else {`,
    `    return '${apiPrefix}'`,
    `  }`,
    `}`,
    '',
  ].join('\n')

  const fileName = `${output}/defaults.ts`
  writeGeneratedContent(fileName, content)
}
