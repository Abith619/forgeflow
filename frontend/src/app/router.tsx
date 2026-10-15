
import { createBrowserRouter } from 'react-router';

import { AppLayout } from '@/app/layouts/AppLayout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { NotFoundPage } from '@/shared/ui/NotFoundPage';
import { PlaceholderPage } from '@/shared/ui/PlaceholderPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <PlaceholderPage title="Dashboard" />,
      },
      {
        path: 'products',
        element: <PlaceholderPage title="Products" />,
      },
      {
        path: 'locations',
        element: <PlaceholderPage title="Locations" />,
      },
      {
        path: 'moves',
        element: <PlaceholderPage title="Moves" />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
