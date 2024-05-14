import {existsSync, mkdirSync, rmSync} from 'fs'

import {
  ApiDescription,
  HttpMethod,
  MethodDesc,
  PropDescription,
} from './interfaces'
import {getImports, tsType, writeGeneratedContent} from './utils'

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

const paramSig = (name: string, required: boolean, schema: PropDescription) => {
  const type = tsType(schema)
  return `${name}${required ? '' : '?'}: ${type}`
}

const genService = (methods: ServiceMethod[]) => {
  let content = ''
  const types = new Set<string>()
  for (const method of methods) {
    // TODO: it is better to search for suitable response, not for a default
    const responseData = method.description.responses['200']

    if (
      responseData.content &&
      'application/octet-stream' in responseData.content
    ) {
      const paramsList = (method.description.parameters ?? []).map(
        (param) => `${paramSig(param.name, param.required, param.schema)}`
      )

      // replace all OpenAPI path parameters with JS template literals
      const interpolatedPath = method.path.replace(/\{(.*)?\}/g, '${$1}')
      const requestParams = paramsList.join(', ')
      const methodName = convertServiceNameToLink(method.description.summary)
      const funcSignature = `(${requestParams}): string`

      content += `export const ${methodName} = ${funcSignature} => {\n`
      content += `  return getApiBase() + \`${interpolatedPath}\`\n`
      content += `}\n`
    } else {
      const respType = responseType(responseData)

      // TODO: this should be done in a smarter way
      if (
        respType != 'any' &&
        respType != 'null' &&
        respType != 'undefined' &&
        !respType.endsWith('[]')
      ) {
        types.add(respType)
      } else if (respType.endsWith('[]')) {
        types.add(respType.slice(0, -2))
      }

      const paramsList = (method.description.parameters ?? []).map(
        (param) => `${paramSig(param.name, param.required, param.schema)}`
      )

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

      if (method.description.requestBody) {
        // TODO: check it smarter, not hardcoded 'multipart/form-data'
        if (isFormData(method.description.requestBody.content)) {
          const schema =
            method.description.requestBody.content['multipart/form-data'].schema
          const type = tsType(schema)
          types.add(type)
          paramsList.push(`data: ${type}`)
        } else if (isJsonData(method.description.requestBody.content)) {
          const schema =
            method.description.requestBody.content['application/json'].schema
          const type = tsType(schema)
          types.add(type)
          paramsList.push(`content: ${type}`)
        } else {
          console.warn('Unknown request body:', method.description.requestBody)
        }
      }

      const requestParams = paramsList.join(', ')

      // replace all OpenAPI path parameters with JS template literals
      const interpolatedPath = method.path.replace(/\{(.*)?\}/g, '${$1}')

      const retVal = respType != 'undefined' ? respType : 'void'
      const funcSignature = `async (${requestParams}): Promise<${retVal}>`

      const mandeType = respType != 'undefined' ? `<${respType}>` : ''
      const methodName = convertServiceName(method.description.summary)

      let functionBody = ''
      if (method.description.requestBody) {
        if (isFormData(method.description.requestBody.content)) {
          // TODO: it should be done smarter, not just hardcoded 'file'
          const fileParamName = 'file'
          const fileParam = `data.${fileParamName}`

          functionBody += `  const formData = new FormData()\n`
          functionBody += `  formData.append('file', ${fileParam})\n`
          functionBody += `  const api = mande(getApiBase() + \`${interpolatedPath}\`)\n`
          functionBody += `  return await api.${method.httpMethod}${mandeType}('', formData)\n`
        } else if (isJsonData(method.description.requestBody.content)) {
          functionBody += `  const api = mande(getApiBase() + \`${interpolatedPath}\`)\n`
          functionBody += `  return await api.${method.httpMethod}${mandeType}(content)\n`
        }
      } else {
        functionBody += `  const api = mande(getApiBase() + \`${interpolatedPath}\`)\n`
        functionBody += `  return await api.${method.httpMethod}${mandeType}('')\n`
      }

      content += `export const ${methodName} = ${funcSignature} => {\n`
      content += `${functionBody}`
      content += `}\n`
    }
  }

  let fileContent = ''
  fileContent += `import {mande} from 'mande'\n\n`
  fileContent += `import {getApiBase} from '../defaults'\n\n`
  fileContent += `${getImports(types, '../schemas/')}`
  fileContent += `${content}`
  return fileContent
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
