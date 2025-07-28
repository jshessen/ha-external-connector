export default [
    {
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: {
                window: 'readonly',
                document: 'readonly',
                console: 'readonly',
                fetch: 'readonly'
            }
        },
        rules: {
            'indent': ['error', 4],
            'linebreak-style': ['error', 'unix'],
            'quotes': ['error', 'single'],
            'semi': ['error', 'always'],
            'no-unused-vars': ['warn', {
                'argsIgnorePattern': '^_',
                'varsIgnorePattern': '^_',
                'caughtErrorsIgnorePattern': '^_',
                'destructuredArrayIgnorePattern': '^_'
            }],
            'no-console': 'off',  // Allow console statements in web development
            'prefer-const': 'error',
            'no-var': 'error',
            'eqeqeq': 'error',
            'curly': 'error'
        },
        ignores: [
            'node_modules/',
            'build/',
            'dist/',
            '*.min.js'
        ]
    }
];
