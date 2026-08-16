import { Suspense } from "react";
import type { Metadata } from "next";
import PanelAdmin from "@/components/PanelAdmin";

export const metadata: Metadata = {
  title: "Administración",
  description:
    "Panel de administración de Frontera Grande: editar y eliminar perfiles.",
  robots: { index: false, follow: false },
};

export default function AdminPage() {
  return (
    <Suspense fallback={null}>
      <PanelAdmin />
    </Suspense>
  );
}