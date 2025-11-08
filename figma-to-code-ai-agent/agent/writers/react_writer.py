from __future__ import annotations
import os, shutil
from typing import List, Tuple
from ..utils.logging import log

SCaffold_FILES = {
    "package.json": '''{
  "name": "generated-ui",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vite": "^5.4.8"
  }
}''',
    "index.html": '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Generated UI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',
    "postcss.config.js": '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}''',
    "tailwind.config.js": '''/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
''',
    "tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "esModuleInterop": true,
    "strict": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["src"]
}''',
    "vite.config.ts": '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});''',
    "src/main.tsx": '''import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);''',
    "src/App.tsx": '''export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Generated UI</h1>
        <p className="opacity-70">
          Your components will appear here. The agent should overwrite this file.
        </p>
      </div>
    </div>
  );
}''',
    "src/index.css": '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root { color-scheme: light; }'''
}

def init_scaffold(out_dir: str):
    os.makedirs(os.path.join(out_dir, "src"), exist_ok=True)
    for rel, content in SCaffold_FILES.items():
        full = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    log(f"[green]Scaffold created in {out_dir}[/green]")

def write_llm_files(out_dir: str, files: List[Tuple[str,str]]):
    for name, content in files:
        if name.startswith("src/") or name.startswith("public/") or name.startswith("index.html"):
            path = os.path.join(out_dir, name)
        else:
            path = os.path.join(out_dir, "src", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"Wrote [cyan]{path}[/cyan]")
