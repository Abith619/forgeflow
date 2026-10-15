
import { NavLink } from 'react-router';

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/products', label: 'Products' },
  { to: '/locations', label: 'Locations' },
  { to: '/moves', label: 'Moves' },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-slate-900 p-5 text-white">
      <h1 className="mb-8 text-xl font-bold">ForgeFlow</h1>

      <nav className="space-y-2" aria-label="Main navigation">
        {links.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                'block rounded-lg px-4 py-3 transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white',
              ].join(' ')
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
