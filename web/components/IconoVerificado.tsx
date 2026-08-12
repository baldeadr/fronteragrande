export default function IconoVerificado({
  className = "",
  title,
}: {
  className?: string;
  title?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-label="Verificado"
      role="img"
      className={className}
      fill="none"
    >
      {title && <title>{title}</title>}
      <circle cx="12" cy="12" r="10.5" fill="currentColor" />
      <path
        d="m7.5 12.2 2.9 2.9 6.1-6.2"
        stroke="#fff"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
