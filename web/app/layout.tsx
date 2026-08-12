import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://fronteragrande.mx";

export const metadata: Metadata = {
  title: {
    default: "Frontera Grande — Base de datos de la escena musical",
    template: "%s · Frontera Grande",
  },
  description:
    "Base de datos interactiva de los proyectos musicales de la frontera grande de Tamaulipas: bandas, DJs y proyectos con enlaces a sus redes.",
  metadataBase: new URL(SITE_URL),
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
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:py-10">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
