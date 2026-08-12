import Image from "next/image";

export default function IconoRed({
  src,
  alt,
  size = 20,
}: {
  src: string;
  alt: string;
  size?: number;
}) {
  return (
    <Image
      src={src}
      alt={alt}
      width={size}
      height={size}
      className="shrink-0"
      unoptimized
    />
  );
}
