import {writeGeneratedContent} from './utils'

export const genDefaults = (output: string, apiPrefix: string): void => {
  let content = ''
  content += `export const getApiBase = () => {\n`
  content += `  if (import.meta.env.DEV) {\n`
  content += `    return 'http://localhost:8000'\n`
  content += `  } else {\n`
  content += `    return '${apiPrefix}'\n`
  content += `  }\n`
  content += `}\n`

  const fileName = `${output}/defaults.ts`
  writeGeneratedContent(fileName, content)
}
