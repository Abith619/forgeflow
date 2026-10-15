
import { Outlet } from 'react-router';
import { Sidebar } from '@/app/layouts/Sidebar';

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-900">
      <Sidebar />

      <main className="min-w-0 flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
