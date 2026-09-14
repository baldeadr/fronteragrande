# Visión del proyecto — Qué es y qué no es

> **Documento de referencia única** para la identidad, el alcance y los límites
> del proyecto. Se actualiza aquí cuando la visión cambia; README.md y AGENTS.md
> resumen y enlazan a este documento. El estilo visual de la marca (logo,
> colores, tipografía) vive en `docs/identidad.md`.

## Qué es

- Una **base de datos interactiva y pública** de los **proyectos musicales de la
  frontera grande de Tamaulipas**: bandas, solistas, DJs, colectivos, proyectos
  de covers y tributos; abierta por diseño a crecer a **otras regiones** y a
  **otras disciplinas artísticas**.
- Un **directorio + feed + perfiles** con previews del contenido y **enlaces
  directos a las redes** de cada proyecto (el *puente*): los proyectos se
  descubren, se escuchan y se ven donde realmente están.
- Un instrumento de **stats de la escena**: categorías, ciudades, estado de
  actividad, huella digital por plataforma (seguidores y reproducciones) y
  **hábitos de consumo** (dominancia por plataforma, ratios de engagement,
  benchmarks por género; ver `docs/habitos_consumo.md`).
- Una **herramienta de detección de actividad**: a partir de internet se
  determina si un proyecto sigue activo (regla de actividad documentada).
- Un **registro de los espacios donde se toca** (venues y lugares de presentación,
  activos e históricos): parte de la historia cultural de la escena, fuente de
  publicaciones de eventos (carteles/toquines) y puente hacia patrocinadores
  locales. Ver `docs/venues.md`.
- Una **pieza del propio universo artístico** (`architecting-a-band`): sirve
  para documentar, **medir y posicionar el proyecto propio** frente a la
  competencia, además de aportar valor público.
- Diseñada **mobile-first**, con **SEO básico** (metadatos, sitemap) y una
  **monetización futura** (AdSense/patrocinios) entendida como **medio** para
  sostener el proyecto, no como objetivo en sí.

## Aspiración de profesionalización

Frontera Grande aspira a contribuir a que la escena musical de la región sea
vista y tratada con mayor seriedad. La plataforma no solo documenta proyectos:
busca construir una base de información, confianza y relaciones que facilite
mejores oportunidades para artistas, venues, promotores, medios y marcas.

Esta aspiración se desarrollará gradualmente mediante:

- **Estándar de presencia profesional:** la verificación y la sincronización
  de contenido funcionan únicamente con páginas (Facebook) y cuentas
  profesionales (Instagram/TikTok); se recomienda que cada proyecto opere con
  cara de proyecto en redes y no con su perfil personal. Este estándar se
  comunica en el formulario de alta, la ayuda para artistas y la página
  Acerca de.
- **Datos confiables:** perfiles verificados, estado de actividad, fuentes y
  estadísticas con fechas claras.
- **Presentación profesional:** perfiles, materiales, eventos y contenido que
  permitan descubrir y contratar proyectos con mayor facilidad.
- **Estándares de eventos:** reglas públicas, producción cuidada, pagos o
  condiciones claras y trato equitativo para los participantes.
- **Reconocimiento de la escena:** awards, showcases y encuentros que valoren
  tanto a artistas como a venues, técnicos, promotores y otros colaboradores.
- **Puente con empresas:** información útil para que patrocinadores evalúen
  audiencias, ciudades, formatos y resultados sin depender de promesas vagas.
- **Evidencia de impacto:** reportes de asistencia, alcance, participación y
  resultados que permitan mejorar cada edición y justificar nuevos apoyos.

La profesionalización no significa favorecer únicamente a los proyectos con más
seguidores. Significa crear procesos más transparentes, oportunidades mejor
organizadas y condiciones que hagan visible el valor cultural y económico de la
escena regional.

## Qué no es

- **No es una plataforma de streaming**: no aloja contenido. Los previews
  (miniaturas, videos, embeds) enlazan y se abren en la plataforma de origen.
- **No es una red social**: la plataforma no publica por el artista. El
  **registro es voluntario y lo hace el propio artista**: crea su perfil y
  **conecta su página de Facebook/Instagram** para verificarlo (OAuth). El
  perfil verificado sincroniza sus posts automáticamente; los proyectos que no
  se registran o no conectan quedan como registros de investigación (curaduría
  del proyecto), sin contenido sincronizado.
- **No inventa datos**: seguidores, reproducciones, fechas, lanzamientos y
  logros siempre tienen fuente (CSV semilla o investigación verificada); lo que
  falta por definir se marca `[PENDIENTE]`.
- **No sustituye a `architecting-a-band`**: aquel es el repositorio documental;
  este es su **versión ejecutable** y estadística, que vive en sincronía con él.
- **No es una app de eventos o boletería**: listar eventos es un registro de la
  escena, no promoción ni venta de boletos.
- **No tiene una taxonomía universal de categorías**: la actual
  (Banda / Solista / DJ / Colectivo / Covers / Tributo) es práctica para la
  escena, y MC / Productor se registran como Solista *por ahora* hasta que la
  base justifique abrir más categorías.
- **No cierra el alcance**: la frontera grande de Tamaulipas es el foco actual;
  el modelo de datos y las decisiones (ciudad base única, categorías, géneros)
  están pensados para expandirse a otras regiones y disciplinas.

## Decisión pendiente

- **Contenido al desvincular una red `[PENDIENTE]`**: definir con los artistas si
  las publicaciones sincronizadas de Meta deben conservarse como histórico,
  ocultarse mientras la cuenta esté desvinculada o eliminarse de forma
  permanente. Mientras se decide, la aplicación conserva las publicaciones ya
  sincronizadas y detiene únicamente la sincronización de contenido nuevo.

## Cómo crece

1. **Frontera grande de Tamaulipas** (foco actual): las ciudades del dropdown
   del formulario (lado MX y lado EE. UU. del Valle de Río Grande).
2. **Registro voluntario de artistas**: cada proyecto puede sumarse por su
   cuenta ("Suma tu proyecto") y verificar su perfil conectando su página;
   esto alimenta la base con contenido real sin depender de la curaduría.
3. **Otras regiones**: cuando la base local esté sana, sumar plazas de México y
   más allá; el modelo de datos ya lo permite (ciudad base única, ranking).
4. **Otras disciplinas artísticas**: la estructura (proyecto → redes → actividad)
   es reutilizable; se ampliará cuando se decida el primer piloto.
5. **Predicciones e inteligencia de datos** `[PENDIENTE]`: cuando la base tenga
   una historia estable y suficiente de actividad, alcance y eventos, se evaluará
   entrenar modelos de machine learning para predecir tendencias de la escena,
   estimar crecimiento por proyecto/ciudad/género, recomendar colaboraciones o
   eventos, y detectar anomalías en métricas. El foco previo sigue siendo la
   calidad, verificación y cobertura de los datos.
6. **Ecosistema de playlists temáticas** `[PROPUESTA]`: a partir de la playlist
   semanal "Descubrimiento Semanal", expandir a listas automáticas por **género**,
   **ciudad/lada**, **clásicos**, **novedades/lanzamientos**, **artistas poco sonados**,
   **categoría** y **eventos en vivo**. Cada playlist es un gancho de descubrimiento
   y un activo medible para mercadotecnia y patrocinios. Detalle en
   `docs/playlist_semanal.md` (sección 6).

## Ranking de alcance y Ligas

El sistema de **ranking de alcance** mide la presencia digital de cada proyecto
y lo clasifica en dos grupos separados para una competición justa.

### Índice universal (oculto, solo admin)
- **Cálculo**: cada señal digital se normaliza contra un **techo de referencia**
  mundial (escala log10) en lugar de contra el máximo local de la escena, y el
  índice 0-100 combina el **70% de la señal dominante** (la de mejor ratio) con
  el **30% de cobertura** (media de ratios; contar 0 las señales ausentes
  penaliza no tener la plataforma).
- **Regla anti-trampa**: cuando hay consumo registrado, la audiencia social
  (IG/FB/TT) no puede superar **consumo real × 3** — una audiencia comprada o
  el perfil de un influencer no infla el índice. Sin consumo no se aplica (falta
  de datos, no evidencia).
- **Anti-shorts (2026-08)**: el `viewCount` del canal de YouTube incluye Shorts
  y puede inflarse fácilmente; por eso las vistas de YouTube cuentan al **60%**
  (`FACTOR_CAPACIDAD_VISTAS_YT`) en la clasificación y en los rankings de alcance
  (consumo/índice), y el alcance de YT prioriza suscriptores sobre vistas. La
  cifra cruda que se muestra en el perfil no cambia.
- **Uso exclusivo**: señal de clasificación automática (umbrales fijos → Ligas).
- **No se expone públicamente** (solo `X-Admin-Token`).

### Clasificación automática (on-the-fly)
Umbrales **fijos y documentados** (no dependen de la composición de la escena):
- **Ligas Mayores**: índice universal **≥ 60**.
- **Emergente**: índice universal **≥ 50** (y < 60).
- **Leyenda de la Frontera**: **manual/editorial** (flag `es_leyenda` en BD + fuente en `notas`).
- **Escena (base)**: índice < 50 (sin nivel calculado).

### Rankings visibles (ordenados por el índice universal)
- Desde 2026-08-30 **no se re-normaliza por liga**: las posiciones
  (`rank_liga` y `rank_universal`) se derivan todas del **índice universal**
  (techos fijos, comparable entre todas las ligas; `lib/servicios.ranking_por_ligas`).
- Cada liga mantiene su propia lista (Escena, Emergente, Ligas Mayores,
  Leyenda de la Frontera) y un ranking universal que las mide a todas a la vez.
- El desglose A (audiencia) / C (consumo) de tarjetas y perfil es **solo
  informativo** (`indices_audiencia_consumo`, 40%/60%); nunca decide el orden.

### Criterio editorial de las Ligas (interno y público)
Las Ligas describen **reconocimiento**, no sostenibilidad económica. Un proyecto
**Emergente** se distingue de la base con audiencia y actividad reales, pero eso
no implica que viva de su música (ni se mide ni se promete); la sostenibilidad
suele llegar recién en **Ligas Mayores**. El índice mide **alcance verificable**
(audiencia, consumo y actividad), nunca ingresos ni fama del momento. Este matiz
está en la página Acerca de y guía la curaduría: un emergente puede frenarse
temporalmente y seguir siendo emergente — es una cualidad, no un titular.

### Techos de referencia (documentados)
```
IG/FB/TT/YT seguidores 50M · YT vistas 10B · Spotify oyentes 20M ·
Spotify seguidores 20M · SoundCloud 1B ·
Bandcamp 1M · Beatport 100K · Mixcloud 50K
```
> **Nota**: los techos son fijos y representan el nivel mundial de cada
> plataforma. Si en el futuro algún artista supera un techo, el ratio se satura
> a 1 (ver `lib/helpers.py:TECHOS_REFERENCIA`). El techo de SoundCloud se subió
> el 2026-09-05 de 10M a 100M y luego a 1B: con 10M y 100M las reproducciones de
> SoundCloud resultaban demasiado baratas de acumular frente a los techos de
> YT/Spotify (es más fácil acumularlas que oyentes o vistas) y podían colocar
> a un artista con métricas medias por encima de artistas con oyentes/vistas
> mucho mayores. El techo de Spotify oyentes se bajó el 2026-09-14 de 50M a
> 20M: un oyente mensual es consumo intencional y no se acumula con autoplay
> (YT) ni scroll (social), así que el techo de 50M lo subvaloraba frente a
> señales pasivas (simulado antes del cambio: 3 ascensos de liga y
> reposiciones suaves, sin cambios de índice en los catalogados históricos).

### Persistencia
- La clasificación se computa **on-the-fly** en cada request (columna `nivel_calculada` en DataFrame).
- `es_leyenda` es un **flag booleano** en BD (`artists.es_leyenda`), editable desde el panel admin.
- La columna `nivel` histórica en BD se mantiene por compatibilidad, pero la lógica
  de ranking usa `nivel_calculado` (umbrales fijos del índice universal).
