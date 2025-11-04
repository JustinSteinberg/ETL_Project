import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [    
		tailwindcss(),
		sveltekit()],
	server: {
		proxy: {
			'/etl': 'http://127.0.0.1:8000',
			'/stats': 'http://127.0.0.1:8000',
			'/data': 'http://127.0.0.1:8000',
			'/download.csv': 'http://127.0.0.1:8000',
			'/series': 'http://127.0.0.1:8000',
			'/map': { target: 'http://127.0.0.1:8000', changeOrigin: true }, // ← add this
		}
		}
});
