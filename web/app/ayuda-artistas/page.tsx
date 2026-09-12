import type { Metadata } from "next";
import Link from "next/link";
import { FACEBOOK_FRONTERA_GRANDE } from "@/lib/contacto";

export const metadata: Metadata = {
  title: "Ayuda para artistas",
  description:
    "Guía sencilla para registrar un proyecto, verificarlo con Facebook e Instagram y sincronizar sus publicaciones en Frontera Grande.",
};

const pasos = [
  {
    numero: "01",
    titulo: "Registra tu proyecto",
    texto:
      "Usa el botón Suma tu proyecto y completa el nombre, categoría, ciudad y enlaces públicos de tus redes. Al terminar podrás abrir el perfil creado.",
  },
  {
    numero: "02",
    titulo: "Reclama y verifica el perfil",
    texto:
      "Entra al perfil y pulsa Conectar y verificar. Facebook abrirá una autorización para confirmar que administras la página del proyecto.",
  },
  {
    numero: "03",
    titulo: "Espera la sincronización",
    texto:
      "Verificar el perfil y traer publicaciones son pasos distintos. Después de verificar, las publicaciones de Facebook e Instagram se incorporan mediante la sincronización automática.",
  },
];

export default function AyudaArtistasPage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3 rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-8">
        <span className="text-xs font-bold tracking-wider text-accent">
          GUÍA PARA ARTISTAS
        </span>
        <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
          Suma tu proyecto y conecta tus redes
        </h1>
        <p className="max-w-2xl text-muted">
          Frontera Grande es un puente hacia tus redes. Tú conservas el control
          de tus cuentas y el contenido siempre permanece en su plataforma de
          origen.
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        {pasos.map((paso) => (
          <article
            key={paso.numero}
            className="flex flex-col gap-2 rounded-xl border border-line bg-surface p-4"
          >
            <span className="text-sm font-bold text-accent">{paso.numero}</span>
            <h2 className="font-bold">{paso.titulo}</h2>
            <p className="text-sm leading-relaxed text-muted">{paso.texto}</p>
          </article>
        ))}
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6">
        <h2 className="text-lg font-bold">¿Por qué verificar tu perfil?</h2>
        <ul className="flex flex-col gap-2 text-sm leading-relaxed text-muted">
          <li>✓ <b className="text-text">Badge de verificado</b> público en tu perfil.</li>
          <li>✓ <b className="text-text">Aparece en &ldquo;Artista de la Semana&rdquo;</b> en nuestras redes sociales.</li>
          <li>✓ Tus publicaciones de <b className="text-text">Facebook e Instagram</b> se sincronizan automáticamente.</li>
          <li>✓ Tu <b className="text-text">foto de perfil</b> se actualiza desde tus redes.</li>
          <li>✓ <b className="text-text">Mayor visibilidad</b> en el directorio de Frontera Grande.</li>
          <li>✓ <b className="text-text">Evitas la eliminación:</b> los proyectos que no se verifican pueden ser borrados después de un período de revisión.</li>
        </ul>
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6">
        <h2 className="text-lg font-bold">
          ¿Por qué una página profesional y no tu perfil personal?
        </h2>
        <ul className="flex flex-col gap-2 text-sm leading-relaxed text-muted">
          <li>✓ La verificación y la sincronización funcionan <b className="text-text">solo con páginas o cuentas profesionales</b>: Facebook con la página de tu proyecto; Instagram y TikTok con cuentas de negocio o creador. Con un perfil personal no se puede conectar tu contenido.</li>
          <li>✓ Una página es <b className="text-text">tu vitrina</b>: foto, portada, enlaces, información y varios administradores. Separa tu identidad artística de tu vida personal.</li>
          <li>✓ <b className="text-text">Venues, promotores y patrocinadores buscan proyectos con cara y con datos.</b> Una página bien armada dice “esto es un proyecto serio” — parte de formalizar la escena.</li>
          <li>✓ Al verificarla <b className="text-text">tomas el control</b> de tu ficha en Frontera Grande: badge, edición propia y posts que llegan solos.</li>
        </ul>
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6">
        <h2 className="text-lg font-bold">Antes de conectar Facebook</h2>
        <ul className="flex flex-col gap-2 text-sm leading-relaxed text-muted">
          <li>• Usa la cuenta personal de Facebook que administra la página del proyecto.</li>
          <li>• Esa cuenta debe tener <b className="text-text">control total</b> de la página.</li>
          <li>• La página de Facebook debe ser la misma que registraste en tu perfil.</li>
          <li>• Acepta todos los permisos que solicite Facebook.</li>
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold">Si aparece un error</h2>
        <details className="group rounded-xl border border-line bg-surface">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold">
            “URL bloqueada”
            <span className="text-lg text-accent transition-transform group-open:rotate-45">+</span>
          </summary>
          <p className="px-4 pb-4 text-sm leading-relaxed text-muted">
            La aplicación necesita que Facebook autorice la conexión. Cierra el
            aviso y vuelve a intentarlo desde el botón del perfil. Si el error
            continúa, la configuración de Meta debe revisarla el administrador
            de Frontera Grande.
          </p>
        </details>
        <details className="group rounded-xl border border-line bg-surface">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold">
            “No se pudo conectar la cuenta”
            <span className="text-lg text-accent transition-transform group-open:rotate-45">+</span>
          </summary>
          <p className="px-4 pb-4 text-sm leading-relaxed text-muted">
            Revisa que estés usando la cuenta que administra la página correcta
            y que tenga control total. Si administras varias páginas, asegúrate
            de autorizar la que corresponde a tu proyecto.
          </p>
        </details>
        <details className="group rounded-xl border border-line bg-surface">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold">
            “Mi perfil está verificado, pero no hay publicaciones”
            <span className="text-lg text-accent transition-transform group-open:rotate-45">+</span>
          </summary>
          <p className="px-4 pb-4 text-sm leading-relaxed text-muted">
            Es normal: la verificación y la sincronización son pasos separados.
            La primera sincronización puede tardar. Cuando esté activa, traerá
            publicaciones recientes de las cuentas conectadas.
          </p>
        </details>
      </section>

      <section className="rounded-xl border border-line bg-surface-2 p-5 text-sm text-muted sm:p-6">
        <p>
          ¿Aún tienes problemas? Vuelve a tu perfil y confirma que los enlaces
          de Facebook e Instagram sean públicos y correspondan al proyecto.
        </p>
        <a
          href={FACEBOOK_FRONTERA_GRANDE}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex text-accent underline underline-offset-2"
        >
          Escribir a Frontera Grande por Facebook
        </a>
        <Link
          href="/artistas"
          className="mt-2 inline-flex rounded-lg bg-accent px-3 py-1.5 font-medium text-bg hover:opacity-90"
        >
          Ir al directorio
        </Link>
        <Link
          href="/notificaciones"
          className="mt-2 inline-flex rounded-lg border border-line px-3 py-1.5 font-medium text-muted hover:border-accent hover:text-text"
        >
          Configurar notificaciones
        </Link>
      </section>
    </div>
  );
}
