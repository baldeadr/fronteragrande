import type { Metadata } from "next";
import { api } from "@/lib/api";
import Directorio from "@/components/Directorio";
import FormAgregarArtista from "@/components/FormAgregarArtista";

export const metadata: Metadata = {
  title: "Directorio de artistas",
  description:
    "Explora la base de datos de la escena de la frontera grande de Tamaulipas: bandas, DJs y proyectos con su estado de actividad y enlaces a redes.",
};

export default async function ArtistasPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const artistas = await api.artists();

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Directorio de artistas</h1>
          <p className="mt-1 text-muted">
            {artistas.length} proyectos de la escena de la frontera grande, de activos a en pausa.
          </p>
        </div>
        <FormAgregarArtista />
      </div>
      <Directorio
        key={q ?? ""}
        artistas={artistas}
        busquedaInicial={q ?? ""}
      />
    </div>
  );
}
