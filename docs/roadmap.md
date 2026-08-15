# Roadmap — Frontera Grande

Estado del proyecto y próximos pasos. Convenciones: ✔ hecho ·
`[PENDIENTE]` esperando datos/definición del artista · `[PROPUESTA]`
propuesta de la IA pendiente de confirmación.

## Fase actual

**Web pública en local (Next.js + FastAPI)**: directorio, perfiles, feed de
actividad interactivo, eventos, **panel de stats interactivo**, **registro
voluntario de artistas** (verificación por OAuth de Meta) y puente a redes,
con página **Acerca de**. **Desplegado en línea (agosto 2026)** con Vercel +
Render + Neon (ver estado completo en `docs/despliegue.md`). Queda pendiente
de **datos externos** (cron de Meta, Extended Quota de Spotify) que el artista
debe conseguir.

## Hecho

| # | Etapa | Detalle |
|---|-------|---------|
| 1 | ✔ MVP original (Streamlit) | CRUD + lista + eventos + stats + scraper. Superado por la web. |
| 2 | ✔ Feed de contenido reciente | Últimos videos de YouTube (RSS, sin API key) unificados con eventos y lanzamientos. |
| 3 | ✔ Pivote a web pública | Next.js + FastAPI, previews y puente a redes, mobile-first, SEO básico. |
| 4 | ✔ Fotos de perfil | URLs desde las redes sin descargar imágenes (`scraper/jerarquias.py`); fallback a inicial. |
| 5 | ✔→✘ Ingesta asistida de posts (eliminada) | Se implementó como puente manual (`POST /api/artists/{slug}/feed` + botón "+ Añadir post") y luego **se eliminó** en el pivote a **registro voluntario del artista**: el contenido del feed solo llega por el artista que conecta su página FB/IG (sync Meta) o el feed de YouTube del onboarding. No reintroducir. |
| 6 | ✔ Stats de redes | Seguidores FB/IG y reproducciones Spotify por plataforma (datos con fuente). |
| 7 | ✔ **Ranking de alcance** | Índice 0-100 = suma ponderada por plataforma (IG 30/FB 25/Spotify 20/YT 10/TT 10/BC 2.5/SC 2.5) de alcance `log10` normalizado entre todos los artistas (`lib/helpers.py`); menciones especiales para el Top 3 por género/ciudad/segmento. |
| 8 | ✔ Directorio pulido + registro desde la web | Taxonomía de categoría (Banda/Solista/DJ/Colectivo/Covers/Tributo; MC y Productor como Solista), ciudades base única con dropdown (Tamaulipas + Valle de Río Grande + "Otro"), filtros con etiqueta y "Todas", géneros en chips; `POST /api/artists` ("Suma tu proyecto") con onboarding (foto, ultimos videos YT, `estado_activo`). El artista **verifica** su perfil conectando la página FB/IG. |
| 9 | ✔ Identidad **Frontera Grande** + Acerca de | Renombrado en toda la web; `docs/vision.md` (fuente única de qué es/qué no es); página **Acerca de** (historia, "cómo explorar", actividad y regla del ranking con fórmula en LaTeX); feed mejorado (foto real, fecha relativa, "Cargar más", H1 "Actividad de la escena"). |
| 10 | ✔ **Panel de stats interactivo** | `GET /api/stats` ampliado (`feed_serie`, `altas_por_mes`, `seguidores`/`reproducciones`, `cobertura`, `posts_90dias`, `por_ciudad`, `eventos_proximos`) + gráficas SVG caseras interactivas (actividad temporal, ranking desglosable por red, ecosistema de redes, ciudades apiladas con leyenda, dona por categoría) — sin dependencias de cliente. |

## Pendiente de datos externos (bloquea su activación)

| # | Etapa | Estado | Depende de |
|---|-------|--------|-----------|
| 11 | **Sincronización automática FB/IG (Meta)** | ◐ OAuth y primera sincronización de producción completados: Apex Ultra quedó **verificado** y sus publicaciones de Facebook ya aparecen en el perfil. Workflow de GitHub Actions activo cada 6 horas. Pendiente conectar al resto de artistas y confirmar el siguiente ciclo automático. | Artistas participantes |
| 12 | YouTube `vistas_yt` | `[PENDIENTE]` no se extraen sin API key o ejecución de JS. | `YOUTUBE_API_KEY` opcional |
| 13 | Spotify: números del API | ✔ MCP (`scripts/spotify_mcp_server.py`) + snapshot (`scripts/escena_local_snapshot.py` → `data/escena_local_stats.csv`) clonados de architecting-a-band y probados. **Verificado 2026-08:** con las credenciales de desarrollo el API resuelve nombre/imagen/URI, pero **no entrega followers/popularity/géneros** (los campos ni siquiera aparecen) y `top-tracks` da **403**; el snapshot ya tolera esa respuesta (registra 0/0) y queda listo para re-ejecutarse sin cambios. **`[PENDIENTE]`** el API 2026 entrega esos números solo con **Extended Quota** (revisión de la app en el dashboard: developer.spotify.com/dashboard → app → solicitar quota). | **Extended Quota** de Spotify |

## Próximas etapas `[PROPUESTA]`

| # | Etapa | Notas |
|---|-------|-------|
| 14 | **Canales oficiales de comunicación** | `[PROPUESTA]` Crear página de Facebook y cuenta de Instagram de Frontera Grande. Publicar artistas registrados, eventos, lanzamientos, datos de la escena y reels con fuentes o autorización; enlazar siempre al sitio. Definir identidad, calendario editorial y métricas de tráfico. |
| 15 | Panel de administración en la web | CRUD de artistas + disparador de scraper, con auth simple. |
| 16 | Feeds de Bandcamp/SoundCloud y métricas públicas de Spotify | Captura puntual de oyentes mensuales desde perfiles públicos de Spotify; 16 URLs confirmadas y 11 artistas sin perfil. Pendiente ejecutar el lote inicial en producción. |
| 17 | Mapa de artistas por origen | PostGIS: la geografía de la escena (Reynosa/Matamoros/frontera). |
| 18 | **Producción y monetización** | ✔ **EN LÍNEA (agosto 2026):** web en Vercel (`fronteragrande.vercel.app`), API en Render (`fronteragrande-api.onrender.com`), BD en Neon. Deploy automático desde GitHub. Meta ya sincroniza publicaciones; pendiente: medir audiencia 90 días, evaluar patrocinio local, monitor UptimeRobot, conectar más artistas, **dominio** (`fronteragrande.mx`) y AdSense. Análisis financiero: `docs/finanzas.md`. |

## En curso `[PROPUESTA]`

| # | Etapa | Estado |
|---|-------|--------|
| 18 | **Despliegue free tier (prueba con artistas)** | ✔ **Activo (2026-08):** API en Render `https://fronteragrande-api.onrender.com` (`{"estado":"ok"}`), web en Vercel `https://fronteragrande.vercel.app`, datos en Neon y Meta sincronizando en producción. Apex Ultra está verificado y muestra publicaciones de Facebook. Pendientes menores: crear monitor UptimeRobot y conectar más artistas (`docs/despliegue.md`). |

## Pendiente de producto

| Ítem | Estado |
|------|--------|
| **Dominio** | Decisión tomada: **`fronteragrande.mx`** (2026-08). Metadatos/sitemap/robots ya usan `https://fronteragrande.mx`. Pendiente: registrar/comprar el dominio y apuntarlo al despliegue. |
| **Permisos del registro** | El formulario hoy es público (modo desarrollo); requiere auth cuando se decida. |
| **Sync de Meta** | Workflow de GitHub Actions activo cada 6 horas; primera sincronización confirmada con Apex Ultra. Pendiente conectar al resto de artistas. |
| **Finanzas** | Análisis inicial en `docs/finanzas.md`: audiencia de nicho, costos casi nulos en free tier, patrocinio local antes que APIs premium y AdSense como complemento. |

## Cómo se actualiza

- Los pasos los decide el **artista**; la IA propone e implementa lo técnico.
- Al completar una etapa, moverla a "Hecho" y actualizar `README.md`
  (sección Roadmap), `AGENTS.md` (Estado) y este documento — una sola verdad.
- Un elemento `[PENDIENTE]` no se marca hecho hasta que el dato real llegue
  y se verifique (regla: no inventar datos).
