import type { Metadata, Viewport } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import NavegacionMovil, { BotonAtras } from "@/components/NavegacionMovil";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://fronteragrande.mx";

export const viewport: Viewport = {
  themeColor: "#0b0b10",
};

export const metadata: Metadata = {
  title: {
    default: "Frontera Grande — Base de datos de la escena musical",
    template: "%s · Frontera Grande",
  },
  description:
    "Base de datos interactiva de los proyectos musicales de la frontera grande de Tamaulipas: bandas, DJs y proyectos con enlaces a sus redes.",
  metadataBase: new URL(SITE_URL),
  appleWebApp: {
    capable: true,
    title: "Frontera Grande",
    statusBarStyle: "black-translucent",
  },
  icons: {
    apple: [
      {
        url: "/icons/apple-touch-icon-180.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
  openGraph: {
    title: "Frontera Grande",
    description:
      "Base de datos de la escena musical de la frontera grande de Tamaulipas.",
    locale: "es_MX",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-bg text-text">
        <Nav />
        <BotonAtras />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 pb-24 sm:py-10 sm:pb-10">
          {children}
        </main>
        <Footer />
        <NavegacionMovil />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ("serviceWorker" in navigator && (location.protocol === "https:" || ["localhost","127.0.0.1"].includes(location.hostname))) {
                addEventListener("load", () => {
                  navigator.serviceWorker.register("/sw.js").catch(() => {});
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
