const niveles: Record<string, { color: string }> = {
  "Ligas Mayores": { color: "#f5b301" },
  "Leyenda de la Frontera": { color: "#8a63d2" },
  "En Ascenso": { color: "#2fb8a6" },
};

export default function InsigniaNivel({
  nivel,
  size = "sm",
}: {
  nivel: string;
  size?: "sm" | "lg";
}) {
  if (!nivel) return null;
  const info = niveles[nivel] ?? { color: "#888" };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 font-medium ${
        size === "lg" ? "py-1 text-sm" : "py-0.5 text-xs"
      }`}
      title={`Liga: ${nivel}`}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: info.color }}
      />
      {nivel}
    </span>
  );
}
