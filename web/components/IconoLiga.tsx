export const INFO_LIGAS: Record<string, string> = {
  "Ligas Mayores": "#f5b301",
  "En Ascenso": "#2fb8a6",
  "Leyenda de la Frontera": "#8a63d2",
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
  if (nivel === "En Ascenso") {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6h-6z" />
      </svg>
    );
  }
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M5 16L3 6l5.5 3.5L12 4l3.5 5.5L21 6l-2 10H5z" />
    </svg>
  );
}