import { APP_NAME } from './shared/lib/app-name';

function App() {
  return (
    <main className="min-h-screen bg-slate-100 p-8">
      <h1 className="text-3xl font-bold text-red-600">
        {APP_NAME}
      </h1>
      <p className="mt-2 text-slate-700">
        React + TypeScript + Tailwind CSS 4
      </p>
    </main>
  );
}

export default App;