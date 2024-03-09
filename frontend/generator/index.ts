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

  fetch(options.input)
    .then((response) => {
      response.json().then((data: ApiDescription) => {
        if (existsSync(options.output)) {
          rmSync(options.output, {recursive: true})
        }
        mkdirSync(options.output, {recursive: true})

        genDefaults(options.output, options.prefix)
        genSchemas(join(options.output, 'schemas'), data.components.schemas)
        genServices(join(options.output, 'services'), data.paths)
      })
    })
    .catch((error) => {
      console.error('Failure:', error)
    })
}

main()
