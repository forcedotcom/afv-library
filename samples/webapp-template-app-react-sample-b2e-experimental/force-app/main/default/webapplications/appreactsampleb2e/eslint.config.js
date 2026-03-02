import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import graphqlPlugin from '@graphql-eslint/eslint-plugin';

export default [
  // Global ignores
  {
    ignores: ['build/**/*', 'dist/**/*', 'coverage/**/*'],
  },
  // Config files and build tools (first to avoid inheritance)
  {
    files: ['*.config.{js,ts}', 'vite.config.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.node,
        __dirname: 'readonly',
        process: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
    },
    rules: {
      '@typescript-eslint/no-var-requires': 'off',
    },
  },
  // Main TypeScript/React files
  {
    files: ['**/*.{ts,tsx}'],
    ignores: [
      'coverage',
      'dist',
      'node_modules',
      'build',
      '*.config.{js,ts}',
      'vite.config.ts',
    ],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      parser: tsparser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: './tsconfig.json',
      },
      globals: {
        ...globals.browser,
        JSX: 'readonly',
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      '@typescript-eslint': tseslint,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react/jsx-no-comment-textnodes': 'off',
      'react/no-unescaped-entities': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  // Test files
  {
    files: [
      '**/*.test.{ts,tsx}',
      '**/test/**/*.{ts,tsx}',
      'src/test/**/*.{ts,tsx}',
    ],
    languageOptions: {
      parser: tsparser,
      globals: {
        ...globals.browser,
        ...globals.node,
        global: 'writable',
        JSX: 'readonly',
      },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  // GraphQL processor - extracts GraphQL from gql template literals in TS/TSX files
  {
    files: ['**/*.{ts,tsx}'],
    processor: graphqlPlugin.processor,
  },
  // GraphQL linting configuration for .graphql files
  {
    files: ['**/*.graphql'],
    languageOptions: {
      parser: graphqlPlugin.parser,
      parserOptions: {
        graphQLConfig: {
          schema: '../../../../../schema.graphql',
        },
      },
    },
    plugins: {
      '@graphql-eslint': graphqlPlugin,
    },
    rules: {
      '@graphql-eslint/no-anonymous-operations': 'error',
      '@graphql-eslint/no-duplicate-fields': 'error',
      '@graphql-eslint/known-fragment-names': 'error',
      '@graphql-eslint/no-undefined-variables': 'error',
      '@graphql-eslint/no-unused-variables': 'error',
    },
  },
];
