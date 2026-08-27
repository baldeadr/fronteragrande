import type { Metadata } from "next";
import {
  FACEBOOK_FRONTERA_GRANDE,
  INSTAGRAM_FRONTERA_GRANDE,
} from "@/lib/contacto";

export const metadata: Metadata = {
  title: "Política de privacidad",
  description:
    "Cómo trata Frontera Grande los datos: qué información se publica, qué se recolecta al conectar redes, las notificaciones push y los derechos de los artistas.",
};

const fecha_actualizacion = "27 de agosto de 2026";

const que_publicamos = [
  "Los datos de los perfiles son públicos y provienen de dos vías: la investigación del proyecto (información ya publicada en internet por los propios artistas) y el registro voluntario del propio proyecto.",
  "Cada perfil muestra el nombre del proyecto, su ciudad base, categoría, géneros, bio, enlaces a sus redes y las métricas públicas de esas redes (seguidores, reproducciones o vistas).",
  "Las métricas no se inventan: siempre tienen fuente, ya sea el propio artista, su página conectada o plataformas públicas.",
  "El feed reproduce publicaciones, videos, lanzamientos y eventos propios de los artistas, con enlace directo a su origen. Frontera Grande no aloja contenido: las previews se abren en su plataforma original.",
];

const registro = [
  "Al registrar un proyecto se pide: nombre del proyecto, ciudad base, categoría, géneros, una bio breve y enlaces a sus redes. Todos estos datos son públicos en la página de cada proyecto.",
  "El registro es voluntario y libre: no se pide correo electrónico, teléfono ni contraseña.",
  "Los proyectos registrados aparecen como «sin verificar» hasta que el artista conecta su página de Facebook, Instagram o TikTok. Los proyectos sin verificar pueden ser eliminados para mantener la calidad del directorio.",
];

const conexion_redes = [
  "Para verificar un proyecto y sincronizar su contenido en tiempo real, el artista puede conectar su página de Facebook/Instagram (Meta) o su cuenta de TikTok mediante autorización OAuth de la propia plataforma.",
  "Con la conexión, Frontera Grande puede leer: las publicaciones de la página/creador, los eventos, la foto de perfil, la bio pública y el número de seguidores. Esa información se muestra en el perfil y en el feed del proyecto.",
  "Los tokens de acceso se guardan de forma segura y nunca se exponen públicamente ni en la API. El artista puede desconectar su página o cuenta en cualquier momento desde su perfil.",
  "Con autorización del artista, el proyecto puede publicar en Instagram (@fronteragrande) una publicación de bienvenida sobre el proyecto recién verificado. Esta función está desactivada por defecto y solo se usa con permiso.",
];

const scraping = [
  "Para determinar el estado de actividad del directorio (activo / en duda / inactivo), Frontera Grande consulta información pública de internet: publicaciones, videos, lanzamientos y eventos recientes de cada proyecto.",
  "Solo se procesa información que los artistas ya hicieron pública. No se accede a perfiles privados ni a datos personales no publicados.",
];

const push = [
  "La aplicación puede enviar notificaciones web push (avisos de nuevas altas, nuevos posts y broadcasts del administrador).",
  "Para eso, el navegador guarda un identificador técnico de la suscripción (endpoint y llaves de cifrado) en la base de datos. No se guarda información personal del dispositivo.",
  "Las notificaciones se pueden desactivar en cualquier momento desde el navegador o desde el propio sitio.",
];

const analitica = [
  "El sitio usa Vercel Analytics para conocer el volumen de visitas de forma agregada. Esta analítica es respetuosa con la privacidad: no usa cookies ni recopila datos personales identificables.",
  "Frontera Grande no vende ni comparte los datos de sus visitantes ni de los artistas con terceros, y actualmente no muestra publicidad de terceros.",
];

const alojamiento = [
  "La web se aloja en Vercel, la API en Render y la base de datos en Neon (PostgreSQL). Los datos pueden transferirse a los servidores de esos proveedores, ubicados en Estados Unidos, con fines de operación y respaldo.",
];

const derechos = [
  "Si eres artista y quieres que se corrija, actualice o elimine la información de tu proyecto, escribe a la página de Frontera Grande en Facebook o por Instagram, indicando el proyecto y el cambio solicitado.",
  "Solicitamos que la corrección venga de la cuenta oficial del proyecto o de su representante; los cambios se hacen lo antes posible.",
];

export default function PrivacidadPage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-8">
        <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
          Política de privacidad
        </h1>
        <p className="mt-1 max-w-2xl text-muted">
          Frontera Grande es una base de datos interactiva y pública de los
          proyectos musicales de la frontera grande de Tamaulipas. Esta página
          explica qué información tratamos, para qué y qué derechos tienes.
          Actualizada el {fecha_actualizacion}.
        </p>
      </section>

      <section
        aria-labelledby="informacion-publica"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="informacion-publica" className="text-base font-bold">
          La información que publicamos
        </h2>
        <ul className="flex flex-col gap-2">
          {que_publicamos.map((q) => (
            <li
              key={q}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {q}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="registro"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="registro" className="text-base font-bold">
          Registro voluntario de artistas
        </h2>
        <ul className="flex flex-col gap-2">
          {registro.map((r) => (
            <li
              key={r}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {r}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="conexion"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="conexion" className="text-base font-bold">
          Conexión de Facebook, Instagram y TikTok
        </h2>
        <ul className="flex flex-col gap-2">
          {conexion_redes.map((c) => (
            <li
              key={c}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {c}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="monitoreo"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="monitoreo" className="text-base font-bold">
          Monitoreo de actividad pública
        </h2>
        <ul className="flex flex-col gap-2">
          {scraping.map((s) => (
            <li
              key={s}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {s}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="notificaciones"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="notificaciones" className="text-base font-bold">
          Notificaciones web push
        </h2>
        <ul className="flex flex-col gap-2">
          {push.map((p) => (
            <li
              key={p}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {p}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="analitica"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="analitica" className="text-base font-bold">
          Analítica y terceros
        </h2>
        <ul className="flex flex-col gap-2">
          {analitica.map((a) => (
            <li
              key={a}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {a}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="alojamiento"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="alojamiento" className="text-base font-bold">
          Alojamiento y transferencia
        </h2>
        <ul className="flex flex-col gap-2">
          {alojamiento.map((a) => (
            <li
              key={a}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {a}
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="derechos"
        className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6"
      >
        <h2 id="derechos" className="text-base font-bold">
          Tus derechos y contacto
        </h2>
        <ul className="flex flex-col gap-2">
          {derechos.map((d) => (
            <li
              key={d}
              className="flex gap-2.5 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">·</span> {d}
            </li>
          ))}
        </ul>
        <p className="flex flex-wrap gap-2 text-sm">
          <a
            href={FACEBOOK_FRONTERA_GRANDE}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-line bg-surface-2 px-3 py-1.5 text-accent hover:border-accent"
          >
            Facebook
          </a>
          <a
            href={INSTAGRAM_FRONTERA_GRANDE}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-line bg-surface-2 px-3 py-1.5 text-accent hover:border-accent"
          >
            Instagram
          </a>
        </p>
      </section>
    </div>
  );
}