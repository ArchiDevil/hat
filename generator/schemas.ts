import {existsSync, mkdirSync, rmSync} from 'fs'

import {ApiDescription, PropDescription} from './interfaces'
import {
  getImports,
  getReferencedType,
  tsType,
  writeGeneratedContent,
} from './utils'

export const genSchemas = (
  output: string,
  schemas: ApiDescription['components']['schemas']
): void => {
  const genProps = (
    props: {[name: string]: PropDescription},
    requiredProps: string[]
  ) => {
    const lines: string[] = []
    for (const propName in props) {
      const prop = props[propName]
      const required = requiredProps.find((val) => propName == val) ? '' : '?'
      lines.push(`  ${propName}${required}: ${tsType(prop)}`)
    }
    return lines
  }

  const getUsedTypes = (properties: {
    [name: string]: PropDescription
  }): string[] => {
    const imports = new Set<string>()
    for (const propName in properties) {
      const prop = properties[propName]
      // TODO: this all thing should be refactored as it on limits of supporting complex schemas
      if ('$ref' in prop) {
        const type = getReferencedType(prop.$ref)
        imports.add(type)
      } else if ('anyOf' in prop) {
        prop.anyOf.map((val) => {
          if ('$ref' in val) {
            imports.add(getReferencedType(val.$ref))
          }
        })
      } else {
        // TODO: make it smarter
        if (prop.type === 'array' && prop.items && '$ref' in prop.items) {
          const type = getReferencedType(prop.items.$ref)
          imports.add(type)
        }
      }
    }
    return Array.from(imports)
  }

  const genSchema = (schema: string) => {
    const schemaDesc = schemas[schema]
    if ('properties' in schemaDesc && schemaDesc.properties) {
      const schemaProperties = schemaDesc.properties
      const types = getUsedTypes(schemaProperties)
      const imports = getImports(types, './')
      if (imports.length > 0) {
        imports.push('')
      }
      const props = genProps(schemaProperties, schemaDesc.required ?? [])
      return [
        ...imports,
        `export interface ${schema} {`,
        ...props,
        `}`,
        '',
      ].join('\n')
    } else if ('enum' in schemaDesc && schemaDesc.enum) {
      const enumValues = schemaDesc.enum.map((val) => `'${val}'`).join(' | ')
      return `export type ${schema} = ${enumValues}\n`
    } else {
      console.warn('Unsupported schema:', schemaDesc)
      return `// No content`
    }
  }

  if (existsSync(output)) {
    rmSync(output, {recursive: true})
  }
  mkdirSync(output, {recursive: true})

  for (const schema in schemas) {
    const fileName = `${output}/${schema}.ts`
    writeGeneratedContent(fileName, genSchema(schema))
  }
}
