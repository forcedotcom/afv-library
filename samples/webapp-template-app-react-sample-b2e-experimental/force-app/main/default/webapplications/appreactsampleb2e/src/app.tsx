import { createBrowserRouter, RouterProvider } from 'react-router';
import { routes } from '@/routes';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/global.css';

// Match Vite base so client-side routes work when deployed under a path (e.g. /lwr/application/ai/c-webapp2/).
// When served at root (e.g. e2e with static serve), use '/' so routes match.
const base = (import.meta.env.BASE_URL ?? '/').replace(/\/$/, '') || '/';
const basename =
  typeof window !== 'undefined' &&
  (window.location.pathname === '/' ||
    !window.location.pathname.startsWith('/lwr/'))
    ? '/'
    : base;
const router = createBrowserRouter(routes, { basename });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
