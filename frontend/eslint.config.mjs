import tsEslint from 'typescript-eslint'
import vueEslint from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

/** @type {import('eslint').Linter.Config[]} */
export default tsEslint.config([
  {
    ignores: [
      'dist/**',
      'eslint.config.mjs',
      'postcss.config.js',
      'tailwind.config.js',
      'vite.config.ts',
      'src/client/**',
      'public/**'
    ],
  },
  ...vueEslint.configs['flat/essential'],
  ...vueEslint.configs['flat/strongly-recommended'],
  ...vueEslint.configs['flat/recommended'],
  tsEslint.configs.recommendedTypeChecked,
  tsEslint.configs.stylisticTypeChecked,
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: '@typescript-eslint/parser',
        projectService: true,
        extraFileExtensions: ['.vue'],
      },
    },
  },
  {
    files: ['**/*.ts'],

    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
])
