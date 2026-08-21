export default function Loading() {
  return (
    <div
      className="flex min-h-[50vh] flex-col items-center justify-center gap-4"
      role="status"
      aria-label="Cargando"
    >
      <div className="relative h-10 w-10">
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-line border-t-accent" />
        <span className="absolute inset-2 rounded-full bg-accent/20 animate-pulse" />
      </div>
      <p className="text-sm text-muted">Cargando escena…</p>
    </div>
  );
}
