export const INFO_LIGAS: Record<string, string> = {
  Escena: "#9d4edd",
  "Ligas Mayores": "#f5b301",
  Emergente: "#2fb8a6",
  "Leyenda de la Frontera": "#aab4c8",
};

export function IconoLiga({
  nivel,
  className,
}: {
  nivel: string;
  className?: string;
}) {
  if (nivel === "Ligas Mayores") {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    );
  }
  if (nivel === "Emergente") {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    );
  }
  if (nivel === "Escena") {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="4" fill="var(--bg)" />
      </svg>
    );
  }
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M5 16L3 6l5.5 3.5L12 4l3.5 5.5L21 6l-2 10H5z" />
    </svg>
  );
}