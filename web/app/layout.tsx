import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import NavegacionMovil from "@/components/NavegacionMovil";
import BannerNotificaciones from "@/components/BannerNotificaciones";
import PlaylistSemanal from "@/components/PlaylistSemanal";

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
      <body className="flex min-h-full flex-col overflow-x-hidden bg-bg text-text">
        <Nav />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 pb-24 sm:py-10 sm:pb-10">
          {children}
        </main>
        <Footer />
        <NavegacionMovil />
        <BannerNotificaciones />
        <PlaylistSemanal />
        <Script id="registro-service-worker" strategy="afterInteractive">
          {`
            if ("serviceWorker" in navigator && (location.protocol === "https:" || ["localhost","127.0.0.1"].includes(location.hostname))) {
              addEventListener("load", () => {
                navigator.serviceWorker.register("/sw.js", {
                  scope: "/",
                  updateViaCache: "none",
                }).catch((err) => { console.error("[SW] registro falló:", err); });
              });
            }
          `}
        </Script>
      </body>
    </html>
  );
}
