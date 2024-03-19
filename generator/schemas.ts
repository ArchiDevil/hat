import {existsSync, mkdirSync, writeFileSync, rmSync} from 'fs'

import {ApiDescription, PropDescription} from './interfaces'
import {autogenPrologue, getImports, getReferencedType, tsType} from './utils'

export const genSchemas = (
  output: string,
  schemas: ApiDescription['components']['schemas']
): void => {
  const genProps = (
    props: {[name: string]: PropDescription},
    requiredProps: string[]
  ) => {
    let content = ''
    for (const propName in props) {
      const prop = props[propName]
      const required = requiredProps.find((val) => propName == val) ? '' : '?'
      content += `  ${propName}${required}: ${tsType(prop)}\n`
    }
    return content
  }

  const getUsedTypes = (properties: {
    [name: string]: PropDescription
  }): string[] => {
    const imports = new Set<string>()
    for (const propName in properties) {
      const prop = properties[propName]
      if ('$ref' in prop) {
        const type = getReferencedType(prop['$ref'])
        imports.add(type)
      } else {
        // TODO: make it smarter
        if (prop.type === 'array' && prop.items && '$ref' in prop.items) {
          const type = getReferencedType(prop.items['$ref'])
          imports.add(type)
        }
      }
    }
    return Array.from(imports)
  }

  const genSchema = (schema: string) => {
    const types = getUsedTypes(schemas[schema].properties)
    const imports = `${getImports(types, './')}`
    const props = genProps(
      schemas[schema].properties,
      schemas[schema].required || []
    )
    return `${autogenPrologue}${imports}export interface ${schema} {\n${props}}\n`
  }

  if (existsSync(output)) {
    rmSync(output, {recursive: true})
  }
  mkdirSync(output, {recursive: true})

  for (const schema in schemas) {
    const fileContent = `${genSchema(schema)}`
    const fileName = `${output}/${schema}.ts`
    writeFileSync(fileName, fileContent)
  }
}
