/** Utilidades de formato y fechas compartidas por la web. */

const MESES = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
];

export function fechaCorta(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}`;
}

export function fechaHora(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const conHora = d.getHours() !== 0 || d.getMinutes() !== 0;
  if (!conHora) return fechaCorta(iso);
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()} · ${h}:${m}`;
}

export function fechaCaptura(iso: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${MESES[d.getMonth()]} ${String(d.getFullYear()).slice(-2)}`;
}

const DIA_MS = 86_400_000;

export function fechaRelativa(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const dias = Math.floor((Date.now() - d.getTime()) / DIA_MS);
  if (dias < 1) return "hoy";
  if (dias === 1) return "ayer";
  if (dias < 7) return `hace ${dias} días`;
  if (dias < 30) {
    const semanas = Math.floor(dias / 7);
    return `hace ${semanas} ${semanas === 1 ? "semana" : "semanas"}`;
  }
  const meses = Math.floor(dias / 30);
  if (meses < 12) return `hace ${meses} ${meses === 1 ? "mes" : "meses"}`;
  const años = Math.floor(dias / 365);
  return `hace ${años} ${años === 1 ? "año" : "años"}`;
}

export function numeroGrande(n: number): string {
  if (n >= 1_000_000) {
    return `${(n / 1_000_000).toLocaleString("es-MX", { maximumFractionDigits: 1 })}M`;
  }
  if (n >= 10_000) {
    return `${(n / 1_000).toLocaleString("es-MX", { maximumFractionDigits: 1 })}K`;
  }
  return n.toLocaleString("es-MX");
}

export function tipoStat(tipo: string): string {
  if (tipo === "seguidores") return "seguidores";
  if (tipo === "vistas") return "vistas";
  if (tipo === "reproducciones") return "reproducciones";
  if (tipo === "oyentes_mensuales") return "oyentes mensuales";
  return tipo;
}

export function etiquetaMes(mesIso: string): string {
  const [y, m] = mesIso.split("-");
  const n = Number(m);
  if (!n) return mesIso;
  const mes = MESES[n - 1];
  if (!mes) return mesIso;
  return `${mes} ${String(Number(y)).slice(-2)}`;
}

export function mesCorto(mesIso: string): string {
  const n = Number(mesIso.split("-")[1]);
  return MESES[n - 1] ?? mesIso;
}
