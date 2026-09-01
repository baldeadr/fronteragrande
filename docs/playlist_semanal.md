# Playlist semanal "Frontera Grande: Descubrimiento Semanal"

> Estado: **EN LÍNEA** (primera corrida: 2026-08-20). Documentación interna de qué es la playlist, cómo se genera y cómo usarla como gancho de mercadotecnia y redes.

## 1. Qué es

Una **playlist pública de Spotify** curada de forma **automática y semanal** con canciones de los proyectos musicales de la frontera grande de Tamaulipas. Es la cara "escuchable" del proyecto Frontera Grande: cada semana rota una selección de temas de los artistas del directorio.

- **Nombre:** Frontera Grande: Descubrimiento Semanal
- **Enlace público:** https://open.spotify.com/playlist/49qIAMVwZCHs5wLo1GLrlz
- **ID de la playlist:** `49qIAMVwZCHs5wLo1GLrlz` (secreto `SPOTIFY_PLAYLIST_ID` en GitHub Actions)
- **Portada:** `web/public/portada-playlist.png` (3000×3000, fuente `portada-playlist.svg`; composición documentada en `docs/identidad.md`)
- **Owner:** cuenta del artista (Adrián Balderas)
- **Se actualiza:** cada lunes 06:00 (workflow `sync-playlist.yml` de GitHub Actions, con disparo manual disponible)
- **Tamaño:** por defecto 24 canciones (`PLAYLIST_TAMANIO`), 2 por artista (`PLAYLIST_CANCIONES_POR_ARTISTA`)

## 2. Cómo se genera

`scripts/generar_playlist_semanal.py` (ver también la entrada en AGENTS.md):

1. Toma los artistas del directorio que tienen perfil de Spotify (**BD = fuente de verdad**).
2. Por artista, busca sus canciones en cadena de fuentes:
   - **top-tracks** (endpoint oficial, preferido);
   - si la app no los recibe (modo desarrollo), **primer tema de sus lanzamientos** (álbumes/sencillos);
   - último recurso, **búsqueda por nombre filtrada por ID exacto** del artista (evita homónimos).
3. Selección **aleatoria**: 1ª canción por artista y relleno hasta `PLAYLIST_TAMANIO` con una segunda de algunos.
4. Rellena la playlist existente con `PUT /playlists/{id}/items` (endpoint `/items`, migración de marzo 2026 — `/tracks` está deprecado).

**Limitación 2026:** las apps de Spotify en **modo desarrollo** no pueden **crear** playlists vía API (403) ni reciben followers/popularity/top-tracks (403/0). La playlist se creó **manualmente** en Spotify y el script solo la rellena. Para levantar esos límites hace falta **Extended Quota** en el dashboard.

## 3. Uso como gancho de mercadotecnia y redes

La playlist es un activo público y periódico: **algo nuevo cada lunes**. Ideas concretas:

- **Compartir en redes** cada lunes: post en FB/IG/TikTok con el enlace y la portada ("Nueva semana, nuevos sonidos de la frontera"). El cambio de contenido da una razón constante para volver.
- **Enlace en bio / linktree:** la playlist como puente de escucha hacia el proyecto.
- **Botón "Seguir en Spotify":** añadir al sitio (Fronteragrande) para que los visitantes la sigan y reciban las rotaciones.
- **Argumento para artistas:** "tu canción puede rotar en la playlist oficial de la escena" — incentivo para registrarse y mantener actividad (los artistas activos con Spotify entran a la rotación).
- **Contenido para historias/Reels:** mostrar la selección de la semana con un track destacado.
- **Colaboraciones/patrocinios futuros:** la playlist es un activo medible (seguidores, reproducciones) para mostrar alcance de la escena.

## 4. Operación

- **Cambiar tamaño/rotación:** variables `PLAYLIST_TAMANIO`, `PLAYLIST_CANCIONES_POR_ARTISTA`, `PLAYLIST_NOMBRE` (env, ver `.env.example`).
- **Forzar una corrida:** GitHub → Actions → "Actualizar playlist semanal" → **Run workflow**.
- **Corrida manual local:** `python scripts/generar_playlist_semanal.py` (necesita `.env` con credenciales y refresh token; `--dry-run` muestra la selección sin tocar la playlist).
- **Regenerar refresh token:** `python scripts/generar_playlist_semanal.py --auth` (borrar antes `scripts/.spotify_playlist_cache.json` para que reabra el navegador), guardar el token nuevo como secreto `SPOTIFY_PLAYLIST_REFRESH_TOKEN`.

## 5. Pendientes

- Solicitar **Extended Quota** en el dashboard de Spotify para recuperar top-tracks reales (hoy la selección usa lanzamientos/búsqueda).
- Decidir la frecuencia de los avisos de la playlist en redes (cada lunes automático o curaduría manual).

---

## 6. Futuras playlists (plan de expansión)

El objetivo es construir un **ecosistema de playlists** que cubra distintas facetas de la escena, aprovechando la misma base de datos y automatización:

| Playlist | Concepto | Fuente de selección | Frecuencia |
|----------|----------|---------------------|------------|
| **Por género** | Rock, electrónica, regional, hip-hop, pop, experimental, etc. | Artistas del directorio etiquetados por género (campo `generos`) | Semanal o quincenal |
| **Por ciudad / lada** | Reynosa, Matamoros, Nuevo Laredo, Río Bravo, Valle Hermoso, lado EE. UU. (McAllen, Brownsville, Harlingen) | `ciudad` base del artista | Mensual |
| **Clásicos de la frontera** | Temas emblemáticos / fundacionales de la escena (histórico) | Curaduría manual + artistas con `estado_activo = inactivo` pero legado | Trimestral |
| **Novedades / Lanzamientos** | Últimos sencillos y álbumes de la semana (feed de lanzamientos) | `scripts/sync_lanzamientos.py` → `feed_items` tipo `lanzamiento` | Semanal (lunes) |
| **Artistas poco sonados / "Joyas ocultas"** | Proyectos con buena música pero bajo alcance (ranking bajo, alta calidad) | `indice_alcance` bajo + señal de actividad reciente | Mensual |
| **Por categoría** | Bandas, Solistas, DJs, Colectivos, Covers, Tributos | Campo `segmento` | Mensual |
| **Eventos en vivo** | Setlists / canciones de artistas con eventos próximos | Tabla `events` + Spotify | Semanal (previa a fin de semana) |

**Notas técnicas:**
- Cada playlist nueva = ID manual en Spotify + secreto `SPOTIFY_PLAYLIST_ID_<NOMBRE>` en GitHub Actions + workflow dedicado (o parametrizar `generar_playlist_semanal.py` con `--playlist`).
- Requiere **Extended Quota** de Spotify para top-tracks reales y métricas (hoy modo desarrollo limita a 403/0).
- La portada seguiría la identidad visual (`docs/identidad.md`) con variante por tipo.
- El script base (`generar_playlist_semanal.py`) ya es reutilizable: filtra artistas por criterio y aplica la misma lógica de selección/anti-duplicados.

**`[PENDIENTE]` plantillas por playlist:** para que el feed de redes no se sienta monótono, se planea que **cada tipo de playlist** (género, época, novedades, ciudad, clásicos…) tenga su **diseño de tarjeta propio**: un selector de plantilla en `publicar_playlist_semanal.py` que cambie el motivo/composición del arte (p. ej. paleta, motivo de fondo, distribución del título) según el tipo, además de su propio banco de hooks. Hoy el arte y los hooks son uno solo para la playlist semanal.

**`[PENDIENTE]` banco de hooks en BD:** los hooks del copy (`_hook_semana` con `HOOKS_FB`/`HOOKS_IG`) viven como arrays hardcodeados en el script. Con más de una playlist eso no escala: se planea migrarlos a una **tabla BD** (`hook_bank`: `plataforma`, tipo/playlist, `texto`, `emoji`, `activo`, `playlist`) y elegir por semana ISO desde ahí, manteniendo la deterministividad. El paso previo es tener el modelo de datos de playlists temáticas (cada playlist = ID manual + secreto + selector de plantilla).

---

## 7. Tarjeta semanal (arte para redes)

Cuando la playlist se anuncia en redes (fila **R** del calendario de publicaciones), el arte es la **tarjeta de "cartel de festival"** que genera `scripts/publicar_playlist_semanal.py`. Composición, estilo y decisiones documentadas aquí para mantener coherencia si se retoca o se extrapola a otros formatos.

### 7.1 Qué es

- **Tamaño:** cuadrado **1080×1080** (feed IG/FB; se publica con el flujo estándar, sin formato vertical).
- **Salida:** `instance/promos/playlist_semanal_<AAAAMMDD>.jpg`.
- **Determinista:** mismo `hash` en cada corrida (mismo input ⇒ misma imagen), así es verificable de forma estable.
- **Run:** `python scripts/publicar_playlist_semanal.py` (`--dry-run` genera la tarjeta sin publicar).

### 7.2 Composición (de arriba abajo)

1. **Fondo radar de la frontera** — retícula GPS, anillos de sonar, barrido radial, cruz central y etiquetas de ciudades (REYNOSA, McALLEN, MATAMOROS, BROWNSVILLE, NUEVO LAREDO); centro del radar alineado al monograma.
2. **Header:** titular **"DESCUBRIMIENTO SEMANAL"** (Archivo Black), subtítulo "nueva rotación de la escena" y, más sutil, la **semana** abreviada (`Semana del 31 AGO, 26`, formato `_formatear_semana`). *Sin* etiqueta "FRONTERA GRANDE · ESCENA" (se retiró por redundancia y para subir el titular).
3. **3 headliners** en fila: foto circular con anillos neón, **nombre** (Archivo Black, display) y **canción** (Inter, acento claro). La tarjeta central va más grande (jerarquía visual).
4. **Franja "TAMBIÉN SUENAN"** (cuadro con borde): hasta 14 artistas en 2 líneas, completado desde la BD (artistas de la escena con Spotify) cuando la selección no llena; cierre "…y más artistas" o "N tracks".
5. **Botón "ESCUCHAR EN SPOTIFY"** (violeta, Inter) y al pie la **marca FG** (monograma + dominio `fronteragrande.mx`, centrados).

### 7.3 Identidad visual

- **Paleta (coherente con el sitio, `docs/identidad.md`):**
  - Acento violeta `#9d4edd` (`ACENTO`) = `--accent` de la web.
  - Acento claro `#e0aaff` (`ACENTO_CLARO`) para subtítulos/texto relevante.
  - Radar violeta `#ba55d3` (`RADAR`) + oscuro `#361e4a` (`RADAR_OSCURO`).
  - Fondo profundo `#100a19` (`RADAR_FONDO`).
  - Todo en gama **violeta** (no cian) para cohesionar con la identidad Frontera Grande.
- **Tipografía dual:**
  - **Archivo Black** (`_fuente`) = display: titular y nombres de artistas. Es la fuente de marca del sitio.
  - **Inter** (`_fuente_texto`) = texto: subtítulo, semana, canciones, franja, botón, dominio y coordenadas del radar. Legibilidad en cuerpo de texto.
  - Archivo Black es ancha: los nombres usan un lazo que reduce el tamaño hasta caber en el ancho de cada tarjeta.
- **Sombra y glow:** `_texto_glow` da sombra direccional + halo para separar el texto del radar.

### 7.4 Decisiones técnicas clave

- **Radar con supersampling 2×:** se dibuja a 2160×2160 y se reduce con **LANCZOS** a 1080. Esto suaviza (antialias real) las líneas diagonales del barrido y los anillos elípticos, que rasterizados a 1080 quedaban dentados/pixelados.
- **Radar visible pero no invasivo:** alphas subidos para que se vean todas las líneas, con una veladura muy ligera (`alpha 12`) para que el radar no compita con textos ni fotos circulares. Equilibrio: se ve la textura, no roba protagonismo.
- **Fotos circulares con supersampling 3×** + máscara al tamaño de la foto: contorno suave (evita bordes dentados).
- **Etiqueta y línea divisoria retiradas:** se eliminaron el kicker "FRONTERA GRANDE · ESCENA" y la línea horizontal que quedaba sobre la tangente superior de los círculos (eran decorativas, no de alineación) para dar aire al header.
- **Semana abreviada** (`31 AGO, 26`): corta y de tamaño reducido (Inter 20, acento claro tenue) porque es contexto, no foco.

### 7.5 No es un Reel ni una historia

La tarjeta es una **imagen de feed cuadrada**. Publicarla como historia 9:16 o Reel, o con audio del banco de IG, se hace **en la app** al momento de publicar (la API de IG publica el contenedor en el formato que se indique; el audio no se adjunta al archivo sino que se enlaza del banco al publicar). El catálogo del banco de IG no incluye las canciones de la escena de la frontera.

### 7.6 Copy para Facebook e Instagram

El copy lo generan `construir_copy_fb(datos)` e `construir_copy_ig(datos)` en el mismo script (lee los datos de `data/playlist_seleccion_semanal.json`). Estructura común:

**Estructura compartida:**
1. **Hook** — frase corta de escena fronteriza con emoji, rotada de un **banco de hooks** (`_hook_semana`): se elige de forma determinista por **semana ISO del año** (misma fecha ⇒ mismo hook; la tarjeta/copy se mantiene estable). Son 6 hooks por plataforma (FB y IG, ambos con emojis; IG con referencias de cruce). Sin "Track de la semana" duplicado: el headliner ya aparece en la lista de tracks.
2. **Nº de tracks en rotación** — `Esta semana en "Frontera Grande: Descubrimiento Semanal" rotan N tracks de la frontera` (se dice "de la frontera" porque en la frontera hay de todo: géneros variados).
3. **Lista de tracks** — los 3 headliners con 🎵.
4. **Más artistas** — hasta 8 más de la lista completa, con los artistas primero y la coletilla al final (`Oxte, They Are Astronauts... y más artistas esta semana.`), o el contador de restantes (`... y N más por descubrir.`).
5. **CTA** — enlace/guardado + "la rotación del próximo lunes" + invitación a **visitar el sitio** tanto para fans como para artistas (`🌐 Descubre y escucha a todos los proyectos de la frontera en fronteragrande.mx` / `¿Tocas o produces? Suma tu proyecto a la escena: fronteragrande.mx`). En FB se indican los dos (fan y artista); en IG la invitación general al sitio.
6. **Semana (registro discreto)** — la fecha abreviada (`Semana del 31 AGO, 26`) va **al final**, antes de hashtags/menciones, solo como registro (no es el foco).
7. **Hashtags / menciones.**

**Facebook (`construir_copy_fb`):**
- Hook: *"Esa canción que no paras de tararear desde el lunes. La que suena distinto cuando cruzas el puente de noche."*
- Cierre CTA: *"¿Tu proyecto ya está en la frontera? Regístralo en fronteragrande.mx"*.
- Hashtags: `#FronteraGrande #EscenaLocal #DescubrimientoSemanal #MusicaFronteriza`.
- Sin menciones `@`.

**Instagram (`construir_copy_ig`):**
- Hook: *"Esa canción que suena a cruzar el puente de noche con las ventanas abajo. 🌉 La que te acompaña en el trayecto Reynosa ↔ McAllen, Matamoros ↔ Brownsville."*
- Incluye **menciones `@handle_ig`** de los artistas seleccionados (campo `handle_ig` de la selección).
- Hashtags ampliados por ciudades: `#FronteraGrande #DescubrimientoSemanal #EscenaLocal #MusicaIndependiente #Tamaulipas #ValleDeTexas #Reynosa #Matamoros #NuevoLaredo #McAllen #Brownsville #MusicaFronteriza #PuenteInternacional`.

---

Última actualización: 2026-08-25.