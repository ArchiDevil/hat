export type TrivialType = 'string' | 'integer' | 'boolean' | 'null' | 'number'

export interface RefDesc {
  $ref: string
}

export interface AnyOfDesc {
  anyOf: [
    | {
        type: TrivialType
      }
    | RefDesc
  ]
}

export interface TrivialDesc {
  type: TrivialType
  title?: string
  format?: string
  pattern?: string
}

export interface ArrayDesc {
  type: 'array'
  items: RefDesc | AnyOfDesc | TrivialDesc
  title?: string
}

export type PropDescription = TrivialDesc | ArrayDesc | RefDesc | AnyOfDesc

export type HttpMethod = 'get' | 'post' | 'put' | 'delete'

export interface ParamDesc {
  name: string
  in: 'query' | 'path' | 'header' | 'cookie'
  required: boolean
  schema: PropDescription
}

export interface MethodDesc {
  tags: string[]
  summary: string
  operationId: string
  parameters?: ParamDesc[]
  requestBody?: {
    content: {
      [contentType: string]: {
        schema: PropDescription
      }
    }
    required: boolean
  }
  responses: {
    [status: string]: {
      description: string
      content?: {
        [contentType: string]: {
          schema: PropDescription
        }
      }
    }
  }
}

export interface SchemaDesc {
  type: string
  title: string
  required?: string[]
  properties?: {
    [name: string]: PropDescription
  }
  enum?: string[]
}

export interface ApiDescription {
  openapi: string
  info: {
    title: string
    version: string
  }
  paths: {
    [path: string]: {
      [method in HttpMethod]: MethodDesc
    }
  }
  components: {
    schemas: {
      [name: string]: SchemaDesc
    }
  }
}
