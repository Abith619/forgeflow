
type PlaceholderPageProps = {
  title: string;
};

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <section>
      <h2 className="text-3xl font-bold">{title}</h2>
      <p className="mt-2 text-slate-600">
        This page is under development.
      </p>
    </section>
  );
}
