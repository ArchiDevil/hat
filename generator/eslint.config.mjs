import tsEslint from 'typescript-eslint'

/** @type {import('eslint').Linter.Config[]} */
export default tsEslint.config(
  {
    ignores: ['eslint.config.mjs'],
  },
  tsEslint.configs.recommendedTypeChecked,
  tsEslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@typescript-eslint/consistent-indexed-object-style': [
        'error',
        'index-signature',
      ],
    },
  }
)
