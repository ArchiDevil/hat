import {existsSync, mkdirSync, rmSync} from 'fs'

import {
  ApiDescription,
  HttpMethod,
  MethodDesc,
  PropDescription,
} from './interfaces'
import {
  getDefaultImports,
  getImports,
  tsType,
  writeGeneratedContent,
} from './utils'

interface ServiceMethod {
  path: string
  httpMethod: HttpMethod
  description: MethodDesc
}

const convertServiceName = (name: string) => {
  // remove all spaces and special characters
  const normalized = name.replace(/[^a-zA-Z0-9]/g, '')

  // convert to camel case
  return `${normalized.charAt(0).toLowerCase()}${normalized.slice(1)}`
}

const convertServiceNameToLink = (name: string) => {
  // remove all spaces and special characters
  const normalized = name.replace(/[^a-zA-Z0-9]/g, '')

  // convert to camel case
  return `get${normalized}Link`
}

const serviceNameFromTag = (tag: string) => {
  const lowered = tag.toLowerCase()
  return `${lowered.charAt(0).toUpperCase()}${lowered.slice(1)}Service`
}

const responseType = (response: MethodDesc['responses'][string]) => {
  if (!response.content) {
    return 'undefined'
  }

  if (!('application/json' in response.content)) {
    console.warn('Unsupported response content:', response.content)
    return 'any'
  }

  const schema = response.content['application/json'].schema
  return tsType(schema)
}

const paramSignature = (
  name: string,
  required: boolean,
  schema: PropDescription
) => {
  const type = tsType(schema)
  return `${name}${required ? '' : '?'}: ${type}`
}

const isFormData = (content: {
  [contentType: string]: {
    schema: PropDescription
  }
}): content is {'multipart/form-data': {schema: PropDescription}} => {
  return 'multipart/form-data' in content
}

const isJsonData = (content: {
  [contentType: string]: {
    schema: PropDescription
  }
}): content is {'application/json': {schema: PropDescription}} => {
  return 'application/json' in content
}

const getMethod = (method: ServiceMethod) => {
  const types: string[] = []

  // TODO: it is better to search for suitable response, not for a default
  const responseData = method.description.responses['200']
  const paramsList = (method.description.parameters ?? [])
    .filter((param) => {
      return param.in == 'path' || param.in == 'query'
    })
    .map((param) => {
      return {
        location: param.in as string,
        signature: `${paramSignature(
          param.name,
          param.required,
          param.schema
        )}`,
        name: param.name,
      }
    })

  if (
    responseData.content &&
    'application/octet-stream' in responseData.content
  ) {
    // replace all OpenAPI path parameters with JS template literals
    const interpolatedPath = method.path.replace(/\{(\w+)\}/g, '${$1}')
    const requestParams = paramsList.map((param) => param.signature).join(', ')
    const methodName = convertServiceNameToLink(method.description.summary)
    const funcSignature = `(${requestParams}): string`

    return {
      types,
      lines: [
        `export const ${methodName} = ${funcSignature} => {`,
        `  return getApiBase() + \`${interpolatedPath}\``,
        `}`,
      ],
    }
  } else {
    const respType = responseType(responseData)

    // TODO: this should be done in a smarter way
    if (
      respType != 'any' &&
      respType != 'null' &&
      respType != 'undefined' &&
      !respType.endsWith('[]')
    ) {
      types.push(respType)
    } else if (respType.endsWith('[]')) {
      types.push(respType.slice(0, -2))
    }

    if (method.description.requestBody) {
      // TODO: check it smarter, not hardcoded 'multipart/form-data'
      if (isFormData(method.description.requestBody.content)) {
        const schema =
          method.description.requestBody.content['multipart/form-data'].schema
        const type = tsType(schema)
        types.push(type)
        paramsList.push({
          location: 'other',
          signature: `data: ${type}`,
          name: 'data',
        })
      } else if (isJsonData(method.description.requestBody.content)) {
        const schema =
          method.description.requestBody.content['application/json'].schema
        const type = tsType(schema)
        types.push(type)
        paramsList.push({
          location: 'other',
          signature: `content: ${type}`,
          name: 'content',
        })
      } else {
        console.warn('Unknown request body:', method.description.requestBody)
      }
    }

    const requestParams = paramsList.map((param) => param.signature).join(', ')

    // replace all OpenAPI path parameters with JS template literals
    const interpolatedPath = method.path.replace(/\{(\w+)\}/g, '${$1}')

    const retVal = respType != 'undefined' ? respType : 'void'
    const funcSignature = `async (${requestParams}): Promise<${retVal}>`

    const mandeType = respType != 'undefined' ? `<${respType}>` : ''
    const methodName = convertServiceName(method.description.summary)

    let functionBody: string[] = []
    if (method.description.requestBody) {
      if (paramsList.filter((param) => param.location == 'query').length > 0) {
        console.warn('Unsupported query parameters with request body')
      }
      if (isFormData(method.description.requestBody.content)) {
        // TODO: it should be done smarter, not just hardcoded 'data.file'
        functionBody = [
          `  const formData = new FormData()`,
          `  formData.append('file', data.file)`,
          `  return await api.${method.httpMethod}${mandeType}(\`${interpolatedPath}\`, formData)`,
        ]
      } else if (isJsonData(method.description.requestBody.content)) {
        functionBody = [
          `  return await api.${method.httpMethod}${mandeType}(\`${interpolatedPath}\`, content)`,
        ]
      }
    } else {
      let query: string | undefined = undefined
      if (paramsList.filter((param) => param.location == 'query').length > 0) {
        query = paramsList
          .filter((param) => param.location == 'query')
          .map((param) => param.name)
          .join(', ')
      }

      const methodParams = !query ? "" : `, {query: {${query}}}`
      functionBody = [
        `  return await api.${method.httpMethod}${mandeType}(\`${interpolatedPath}\`${methodParams})`,
      ]
    }

    return {
      types,
      lines: [
        `export const ${methodName} = ${funcSignature} => {`,
        ...functionBody,
        '}',
      ],
    }
  }
}

const genService = (methods: ServiceMethod[]) => {
  let lines: string[] = []
  const types = new Set<string>()
  for (const method of methods) {
    const res = getMethod(method)
    res.types.forEach((t) => types.add(t))
    lines = [...lines, ...res.lines]
  }

  const imports = getImports(types, '../schemas/')
  if (imports.length > 0) {
    imports.push('')
  }

  return [...getDefaultImports(), ...imports, ...lines, ''].join('\n')
}

export const genServices = (
  output: string,
  paths: ApiDescription['paths']
): void => {
  if (existsSync(output)) {
    rmSync(output, {recursive: true})
  }
  mkdirSync(output, {recursive: true})

  // group services by tags
  const servicesByTag = new Map<string, ServiceMethod[]>()
  for (const path in paths) {
    const methods = paths[path]
    for (const method in methods) {
      const methodDesc = methods[method as HttpMethod]
      const tags = methodDesc.tags
      for (const tag of tags) {
        if (!servicesByTag.has(tag)) {
          servicesByTag.set(tag, [])
        }
        servicesByTag.get(tag)!.push({
          path: path,
          httpMethod: method as HttpMethod,
          description: methodDesc,
        })
      }
    }
  }

  // generator actual code for every service
  for (const [tag, methods] of servicesByTag) {
    const fileContent = genService(methods)
    const fileName = `${output}/${serviceNameFromTag(tag)}.ts`
    writeGeneratedContent(fileName, fileContent)
  }
}
