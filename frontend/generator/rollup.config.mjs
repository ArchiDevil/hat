import terser from '@rollup/plugin-terser'
import commonjs from '@rollup/plugin-commonjs'
import resolve from '@rollup/plugin-node-resolve'

export default {
  input: 'dist/index.js',
  output: [
    {
      file: 'dist/bundle.mjs',
      format: 'es',
    },
  ],
  plugins: [commonjs(), resolve(), terser()],
}
