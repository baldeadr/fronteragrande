const estados: Record<string, { etiqueta: string; color: string }> = {
  activo: { etiqueta: "Activo", color: "var(--activo)" },
  en_duda: { etiqueta: "En duda", color: "var(--en-duda)" },
  inactivo: { etiqueta: "Inactivo", color: "var(--inactivo)" },
};

export default function EstadoBadge({
  estado,
  size = "sm",
}: {
  estado: string;
  size?: "sm" | "lg";
}) {
  const info = estados[estado] ?? { etiqueta: estado, color: "#888" };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 font-medium ${
        size === "lg" ? "py-1 text-sm" : "py-0.5 text-xs"
      }`}
      title={`Estado de actividad: ${info.etiqueta}`}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: info.color }}
      />
      {info.etiqueta}
    </span>
  );
}
