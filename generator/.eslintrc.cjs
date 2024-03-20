module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended-type-checked',
    'plugin:@typescript-eslint/stylistic-type-checked',
  ],
  overrides: [
    {
      files: ['*.ts'],
      rules: {
        '@typescript-eslint/consistent-indexed-object-style': [
          'error',
          'index-signature',
        ],
      },
    },
  ],
  ignorePatterns: ['.eslintrc.cjs'],
  parserOptions: {
    project: './tsconfig.json',
  },
}
