import type { RouteObject } from 'react-router';
import AppLayout from './appLayout';
import Home from './pages/Home';
import NotFound from './pages/NotFound';
import Maintenance from "./pages/Maintenance";
import Properties from "./pages/Properties";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Home />,
        handle: { showInNavigation: true, label: "Home" }
      },
      {
        path: '*',
        element: <NotFound />
      },
      {
        path: "maintenance",
        element: <Maintenance />,
        handle: { showInNavigation: true, label: "Maintenance" }
      },
      {
        path: "properties",
        element: <Properties />,
        handle: { showInNavigation: true, label: "Properties" }
      }
    ]
  }
];
