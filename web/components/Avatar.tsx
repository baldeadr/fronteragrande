import Image from "next/image";

export default function Avatar({
  src,
  nombre,
  size = 64,
  className = "",
}: {
  src: string | null;
  nombre: string;
  size?: number;
  className?: string;
}) {
  const inicial = nombre ? nombre[0].toUpperCase() : "♪";

  if (!src) {
    return (
      <div
        className={`grid shrink-0 place-items-center rounded-full bg-accent-soft font-bold text-accent ${className}`}
        style={
          className
            ? undefined
            : { width: size, height: size, fontSize: size * 0.4 }
        }
      >
        {inicial}
      </div>
    );
  }

  return (
    <Image
      src={src}
      alt={`Foto de perfil de ${nombre}`}
      width={size}
      height={size}
      className={`shrink-0 rounded-full object-cover ${className}`}
      unoptimized
    />
  );
}
