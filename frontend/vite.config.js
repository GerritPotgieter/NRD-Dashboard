import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    // Load env file based on `mode` in the current working directory.
    const env = loadEnv(mode, process.cwd(), '');

    return {
        plugins: [react()],

        // Path resolution
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },

        // Define global variables for compatibility with CRA
        define: {
            'process.env.REACT_APP_BACKEND_URL': JSON.stringify(env.REACT_APP_BACKEND_URL || 'http://localhost:8000'),
            'process.env.REACT_APP_ENABLE_VISUAL_EDITS': JSON.stringify(env.REACT_APP_ENABLE_VISUAL_EDITS || 'false'),
            'process.env.NODE_ENV': JSON.stringify(mode),
        },

        // Development server configuration
        server: {
            port: 3000,
            host: true, // Listen on all addresses for EC2 deployment
            proxy: {
                '/api': {
                    target: env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
                    changeOrigin: true,
                    secure: false,
                },
            },
        },

        // Build configuration for production
        build: {
            outDir: 'build',
            sourcemap: false,
            // Optimize chunk size for better performance
            rollupOptions: {
                output: {
                    manualChunks: {
                        'react-vendor': ['react', 'react-dom', 'react-router-dom'],
                        'ui-vendor': ['lucide-react', '@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
                        'chart-vendor': ['recharts'],
                        'table-vendor': ['@tanstack/react-table'],
                    },
                },
            },
            chunkSizeWarningLimit: 1000,
        },

        // Preview server (for testing production build locally)
        preview: {
            port: 3000,
            host: true,
            proxy: {
                '/api': {
                    target: env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
                    changeOrigin: true,
                    secure: false,
                },
            },
        },
    };
});
