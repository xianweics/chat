import { createBrowserRouter, Navigate } from 'react-router-dom';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Chat from '../pages/Chat';
import AuthGuard from '../components/AuthGuard';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />
  },
  {
    path: '/login',
    element: (
      <AuthGuard requireAuth={false}>
        <Login />
      </AuthGuard>
    )
  },
  {
    path: '/register',
    element: (
      <AuthGuard requireAuth={false}>
        <Register />
      </AuthGuard>
    )
  },
  {
    path: '/chat',
    element: (
      <AuthGuard requireAuth={true}>
        <Chat />
      </AuthGuard>
    )
  }
]);

export default router; 