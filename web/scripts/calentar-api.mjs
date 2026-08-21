// Calienta la API antes del build (npm ejecuta este archivo vía "prebuild").
// El free tier de Render duerme el servicio y Neon suspende la BD tras unos
// minutos de inactividad: las primeras consultas fallan con 500 mientras
// despiertan. Pedir un endpoint que toque la BD hasta que responda evita que
// el prerender de las páginas estáticas choque con ese arranque en frío.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const MAX_INTENTOS = 18;
const ESPERA_MS = 5000;

const dormir = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let ok = false;
for (let intento = 1; intento <= MAX_INTENTOS && !ok; intento += 1) {
  try {
    const res = await fetch(`${API_URL}/api/artists`);
    ok = res.ok;
    console.log(`[calentar-api] intento ${intento}: HTTP ${res.status}`);
  } catch (error) {
    console.log(
      `[calentar-api] intento ${intento}: sin respuesta (${error?.cause?.code ?? error?.message})`,
    );
  }
  if (!ok && intento < MAX_INTENTOS) await dormir(ESPERA_MS);
}

if (!ok) {
  console.warn(
    "[calentar-api] la API no respondió a tiempo; el build continúa y los reintentos por página toman el relevo.",
  );
}
process.exit(0);
