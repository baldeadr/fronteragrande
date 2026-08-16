import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Notificaciones",
  description:
    "Cómo activar las notificaciones de Frontera Grande para recibir avisos sobre artistas nuevos y contenido reciente.",
};

const plataformas = [
  {
    id: "iphone",
    titulo: "iPhone (Safari)",
    requisito: "iOS 16.4 o posterior",
    pasos: [
      "Abre Frontera Grande en Safari.",
      'Toca el botón de compartir (cuadro con flecha) y selecciona "Añadir a pantalla de inicio".',
      'Confirma con "Añadir".',
      "Abre la app desde el icono de la pantalla de inicio.",
      "Baja hasta el Footer y toca Activar junto a Notificaciones.",
      "Confirma el diálogo de permiso de Safari.",
    ],
    nota:
      "Las notificaciones en iPhone solo funcionan desde la PWA instalada, no desde Safari directamente.",
  },
  {
    id: "android",
    titulo: "Android (Chrome)",
    requisito: "Android 5+ con Chrome",
    pasos: [
      "Abre Frontera Grande en Chrome.",
      "Baja hasta el Footer y toca Activar junto a Notificaciones.",
      'Confirma el diálogo de permiso tocando "Permitir".',
    ],
    nota:
      "No es necesario instalar la PWA; funciona directamente desde el navegador.",
  },
  {
    id: "escritorio",
    titulo: "Escritorio (Chrome, Firefox, Edge)",
    requisito: "Navegador moderno con soporte push",
    pasos: [
      "Abre Frontera Grande en tu navegador.",
      "Baja hasta el Footer y toca Activar junto a Notificaciones.",
      "Confirma el diálogo de permiso.",
    ],
    nota:
      "El aviso se abrirá en la esquina superior derecha de la pantalla.",
  },
];

export default function NotificacionesPage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3 rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-8">
        <span className="text-xs font-bold tracking-wider text-accent">
          NOTIFICACIONES
        </span>
        <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
          Recibe avisos de la escena
        </h1>
        <p className="max-w-2xl text-muted">
          Cuando un artista se registra o publica contenido nuevo, te avisamos.
          Elige tu plataforma y sigue los pasos.
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        {plataformas.map((p) => (
          <article
            key={p.id}
            className="flex flex-col gap-2 rounded-xl border border-line bg-surface p-4"
          >
            <h2 className="font-bold">{p.titulo}</h2>
            <span className="text-xs text-muted">{p.requisito}</span>
            <ol className="flex flex-col gap-1 text-sm leading-relaxed text-muted">
              {p.pasos.map((paso, i) => (
                <li key={i}>
                  <span className="mr-1 font-bold text-accent">{i + 1}.</span>
                  {paso}
                </li>
              ))}
            </ol>
            {p.nota && (
              <p className="mt-1 rounded-lg bg-accent-soft px-3 py-2 text-xs text-accent">
                {p.nota}
              </p>
            )}
          </article>
        ))}
      </section>

      <section className="rounded-xl border border-line bg-surface p-5 sm:p-6">
        <h2 className="mb-2 text-lg font-bold">¿Qué avisos recibirás?</h2>
        <ul className="flex flex-col gap-1 text-sm leading-relaxed text-muted">
          <li>• Artista nuevo registrado en la escena.</li>
          <li>• Publicaciones recientes de artistas conectados (Facebook / Instagram).</li>
        </ul>
      </section>

      <section className="rounded-xl border border-line bg-surface-2 p-5 text-sm text-muted sm:p-6">
        <p>
          ¿No aparece el botón de Notificaciones en el Footer? En iPhone,
          asegúrate de haber instalado la PWA primero (paso 2).
        </p>
        <Link
          href="/ayuda-artistas"
          className="mt-3 inline-flex rounded-lg bg-accent px-3 py-1.5 font-medium text-bg hover:opacity-90"
        >
          Ver guía completa
        </Link>
      </section>
    </div>
  );
}
