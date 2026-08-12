export default function IconoMencion({
  tipo,
  className = "",
}: {
  tipo: "genero" | "categoria" | "ciudad" | "escena";
  className?: string;
}) {
  const comun = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  } as const;
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      aria-hidden="true"
      className={className}
      {...comun}
    >
      {tipo === "escena" ? (
        <>
          <circle cx="12" cy="8" r="6" />
          <path d="M8.21 13.89 7 23l5-3 5 3-1.21-9.12" />
        </>
      ) : tipo === "genero" ? (
        <>
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </>
      ) : tipo === "categoria" ? (
        <>
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.83z" />
          <line x1="7" y1="7" x2="7.01" y2="7" />
        </>
      ) : (
        <>
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
          <circle cx="12" cy="10" r="3" />
        </>
      )}
    </svg>
  );
}
