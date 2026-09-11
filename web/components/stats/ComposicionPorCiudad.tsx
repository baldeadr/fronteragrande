"use client";

/** Composición por ciudad con conmutador liga/género.
 *
 * Una sola tarjeta para dos desgloses de la misma base (ciudad × atributo):
 * un conmutador segmentado alterna entre las ligas y el género dominante sin
 * duplicar la gráfica en la página.
 */

import { useState } from "react";
import DesglosePorCiudad, {
  type AtributoDesglose,
  type FilaDesglose,
} from "@/components/stats/DesglosePorCiudad";

type Vista = "ligas" | "genero";

export default function ComposicionPorCiudad({
  filasLigas,
  atributosLigas,
  filasGeneros,
  atributosGeneros,
}: {
  filasLigas: FilaDesglose[];
  atributosLigas: AtributoDesglose[];
  filasGeneros: FilaDesglose[];
  atributosGeneros: AtributoDesglose[];
}) {
  const [vista, setVista] = useState<Vista>("ligas");

  const vistas: { clave: Vista; etiqueta: string }[] = [
    { clave: "ligas", etiqueta: "Por liga" },
    { clave: "genero", etiqueta: "Por género" },
  ];

  return (
    <div>
      <div className="mb-4 inline-flex rounded-lg border border-line bg-surface-2 p-0.5">
        {vistas.map((v) => {
          const activo = vista === v.clave;
          return (
            <button
              key={v.clave}
              onClick={() => setVista(v.clave)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                activo
                  ? "bg-accent text-bg"
                  : "text-muted hover:text-text"
              }`}
            >
              {v.etiqueta}
            </button>
          );
        })}
      </div>

      {vista === "ligas" ? (
        <DesglosePorCiudad filas={filasLigas} atributos={atributosLigas} />
      ) : (
        <DesglosePorCiudad filas={filasGeneros} atributos={atributosGeneros} />
      )}
    </div>
  );
}