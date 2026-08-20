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

Última actualización: 2026-08-20.