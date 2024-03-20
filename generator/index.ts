import commandLineArgs from 'command-line-args'
import {existsSync, mkdirSync, rmSync} from 'fs'
import {join} from 'path'

import {ApiDescription} from './interfaces'
import {genDefaults} from './defaults'
import {genSchemas} from './schemas'
import {genServices} from './services'

function main() {
  const options = commandLineArgs([
    {name: 'input', alias: 'i', type: String},
    {name: 'prefix', alias: 'p', type: String, defaultValue: ''},
    {name: 'output', alias: 'o', type: String},
  ])

  const input = options.input as string
  const output = options.output as string
  const prefix = options.prefix as string

  fetch(input)
    .then((response) => {
      response
        .json()
        .then((data: ApiDescription) => {
          if (existsSync(output)) {
            rmSync(output, {recursive: true})
          }
          mkdirSync(output, {recursive: true})

          genDefaults(output, prefix)
          genSchemas(join(output, 'schemas'), data.components.schemas)
          genServices(join(output, 'services'), data.paths)
        })
        .catch((error) => {
          console.error('Failure:', error)
        })
    })
    .catch((error) => {
      console.error('Failure:', error)
    })
}

main()
