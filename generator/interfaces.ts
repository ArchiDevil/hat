export interface RefDesc {
  $ref: string
}

export interface AnyOfDesc {
  anyOf: [
    {
      type: 'string' | 'integer' // | 'boolean' // TODO: check if boolean is possible
    }
  ]
}

export interface TrivialDesc {
  type: 'string' | 'integer' // | 'boolean' // TODO: check if boolean is possible
  title?: string
  format?: string
}

export interface ArrayDesc {
  type: 'array'
  items: RefDesc | AnyOfDesc
  title?: string
}

// TODO: check if AnyOfDesc is possible here without an array
export type PropDescription = TrivialDesc | ArrayDesc | RefDesc

export type HttpMethod = 'get' | 'post' | 'put' | 'delete'

export interface ParamDesc {
  name: string
  in: 'query' | 'path' | 'header'
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
