import { IconoLiga, INFO_LIGAS } from "./IconoLiga";

export default function InsigniaNivel({
  nivel,
  size = "sm",
  className = "",
}: {
  nivel: string;
  size?: "sm" | "lg";
  className?: string;
}) {
  if (!nivel) return null;
  const color = INFO_LIGAS[nivel] ?? "#888";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 font-medium ${className} ${
        size === "lg" ? "py-1 text-sm" : "py-0.5 text-xs"
      }`}
      title={`Liga: ${nivel}`}
    >
      <span style={{ color }}>
        <IconoLiga
          nivel={nivel}
          className={size === "lg" ? "h-3.5 w-3.5" : "h-3 w-3"}
        />
      </span>
      {nivel}
    </span>
  );
}
