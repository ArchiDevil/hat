import {globalIgnores} from 'eslint/config'
import tsEslint from 'typescript-eslint'
import vueEslint from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

/** @type {import('eslint').Linter.Config[]} */
export default tsEslint.config([
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,vue}'],
  },
  globalIgnores([
    'dist/**',
    'eslint.config.mjs',
    'postcss.config.js',
    'tailwind.config.js',
    'vite.config.ts',
    'src/client/**',
    'public/**',
  ]),
  ...vueEslint.configs['flat/recommended'],
  tsEslint.configs.recommendedTypeChecked,
  tsEslint.configs.stylisticTypeChecked,
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsEslint.parser,
        projectService: true,
        extraFileExtensions: ['.vue'],
      },
    },
    rules: {
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
    },
  },
  {
    files: ['**/*.ts'],
    languageOptions: {
      parserOptions: {
        projectService: true,
      },
    },
  },
])
