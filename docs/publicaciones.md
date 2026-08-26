# Publicaciones en redes — Frontera Grande

Calendario editorial y bitácora de publicaciones orgánicas (IG/FB).
El arte se genera con `scripts/generar_carruseles.py`; el stock compartido
vive en `carrousel/fuentes/` (prompts documentados en `prompt_images.txt`).

## Convenciones

- Formato: carrusel cuadrado 1080×1080 (los verticales 1080×1920 quedan
  reservados para historias).
- Cadencia inicial: 2 publicaciones/semana (mar + jue/domingo), ajustar con
  métricas tras dos semanas.
- Los posts de bienvenida a artistas verificados son automáticos
  (`lib/promo_fg.py`) y no forman parte de este calendario. La publicación
  es directa en FB e IG cuando `PROMO_AUTO_PUBLISH=true` y `PROMO_IG=true`.
- No mencionar TikTok en publicaciones hasta que salga del sandbox.

## Calendario

| # | Fecha/hora propuesta | Publicación | Arte | Estado |
|---|----------------------|-------------|------|--------|
| 1 | dom 23 ago 2026 · 22:30 | Presentación de Frontera Grande | `carrousel/presentacion/` | ✅ Publicada |
| 2 | mar 25 ago 2026 · 20:30–21:00 | Verifica tu perfil (artistas) | `carrousel/artistas-verifica/` | ✅ Programada |
| 3 | vie 28 ago 2026 · 22:30 | Para los fans: descubre, playlist semanal, avisos | `carrousel/fans/` | ✅ Programada |
| 4 | mar 1 sep 2026 · 20:30 | Tip: pasa tus cuentas a profesional (IG/FB) y sus beneficios | `carrousel/tips/` (2 tarjetas Pillow) | 🔜 Pendiente |
| R | cada lunes (cuando exista) | Anuncio de la playlist semanal de Spotify | — | 💡 Recurrente |

Ideas en reserva: mapa de ciudades con artistas registrados · "cómo usar el
directorio" (filtros género/ciudad) · destacado mensual de eventos.

## Bitácora de copy

### #1 — Presentación (dom 23 ago 2026)

Copy usado en la publicación original (recuperar de Meta Business Suite si
no quedó archivado).

### #2 — Verifica tu perfil (artistas)

**Instagram:**

```text
🎵 ¿Haces música en la frontera? Esto es para ti.

Estamos construyendo el directorio de la escena musical de la
frontera norte de Tamaulipas y el Valle de Texas. Muchos proyectos
ya están listados — y quizá uno de ellos eres tú.

🔍 Búscate en fronteragrande.mx y reclama tu perfil
✍️ ¿No apareces? Regístralo gratis en 2 minutos
✔️ Conecta tu Facebook o Instagram para verificarte

📲 Tus posts llegan solos a tus fans
📅 Tus toquines entran a la agenda de eventos
📣 Te promovemos en nuestras redes al verificarte

Gratis, sin algoritmo que decida quién suena.

👉 Link en bio

#FronteraGrande #EscenaLocal #MusicaIndependiente #Tamaulipas
#ValleDeTexas #Reynosa #Matamoros #NuevoLaredo #McAllen #Brownsville
```

**Facebook:**

```text
🎵 ¿Haces música en la frontera norte de Tamaulipas o el Valle de Texas?

Quizá tu proyecto ya está en nuestro directorio: búscate en
fronteragrande.mx y reclama tu perfil. Si no apareces, regístralo
gratis en 2 minutos y verifícalo conectando tu página de Facebook
o Instagram.

Tus posts llegan solos a tus fans, tus toquines entran a la agenda,
y nosotros te promovemos al verificarte. Gratis, sin algoritmo.

#FronteraGrande #EscenaLocal
```

### #4 — Tip: pasa tu cuenta a profesional (mar 1 sep 2026)

Arte en `carrousel/tips/` (2 tarjetas Pillow 1080×1080: gancho + beneficios).
Script: `scripts/generar_tarjeta_tip.py`.

**Instagram:**

```text
¿Tu cuenta de Instagram es profesional? 📊

Si todavía usas cuenta personal, estás perdiendo datos
que te ayudan a crecer.

Beneficios de cambiar a cuenta profesional (o de creador):

✅ Estadísticas: quién ve tu contenido, de dónde son, cuándo conectan
✅ Botón de contacto: que te llamen, escriban o manden email directo
✅ Programar posts: publica cuando tu audiencia esté en línea
✅ Aparecer en recomendaciones: el algoritmo favorece cuentas profesionales

¿Cómo hacerlo?
1. Ve a tu perfil → Menú (☰) → Configuración
2. Cuenta → Cambiar a cuenta profesional
3. Elige "Músico" o "Artista musical"
4. Conecta tu Facebook (si tienes página)

Toma 2 minutos y no pierdes nada. Lo que sí pierdes es información
valiosa si no lo haces.

¿Ya lo hiciste? Cuéntanos en los comentarios 👇

#FronteraGrande #TipParaArtistas #EscenaLocal #MusicaIndependiente
#InstagramProfesional #Tamaulipas #ValleDeTexas
```

**Facebook:**

```text
¿Tu cuenta de Instagram sigue siendo personal? 📊

Cambiarla a profesional (o de creador) te da datos reales
sobre tu audiencia, botón de contacto y la posibilidad de
programar publicaciones. Toma 2 minutos.

1. Perfil → ☰ → Configuración
2. Cuenta → Cambiar a cuenta profesional
3. Elige "Músico" o "Artista musical"
4. Conecta tu página de Facebook

¿Necesitas ayuda? Te guiamos: fronteragrande.mx/ayuda-artistas

#FronteraGrande #EscenaLocal
```

**Story (opcional):**
- Fondo: slide gancho como imagen
- Texto: "¿Tu IG es profesional? Toca para ver por qué importa"
- Sticker enlace: `/ayuda-artistas`

---

## Aprendizajes

(Registrar tras cada publicación: hora con mejor alcance, formato que rinde,
copy que trae clics. Sin datos aún.)

---

### #R — Playlist semanal (template recurrente, cada lunes)

**Instagram (post fijo + Story opcional):**

```text
Nueva semana, nuevos sonidos de la frontera 🎵

Esta semana en "Frontera Grande: Descubrimiento Semanal":
{TRACK_1} — {ARTIST_1}
{TRACK_2} — {ARTIST_2}
{TRACK_3} — {ARTIST_3}
... y {N} tracks más de la escena.

🎧 Escucha completa: https://open.spotify.com/playlist/49qIAMVwZCHs5wLo1GLrlz
👉 Síguela para que no te pierdas la rotación del próximo lunes.

#FronteraGrande #DescubrimientoSemanal #EscenaLocal #MusicaIndependiente
#Tamaulipas #ValleDeTexas #Reynosa #Matamoros #NuevoLaredo #McAllen #Brownsville
```

**Story (plantilla):**
- Fondo: portada de la playlist (`web/public/portada-playlist.png`)
- Texto: "Nueva selección del lunes 👇"
- Sticker enlace: playlist Spotify
- Poll: "¿Cuál te late más? 1️⃣ {ARTIST_1} · 2️⃣ {ARTIST_2}"

**Facebook:**

```text
Cada lunes, una selección fresca de la escena musical de la frontera
norte de Tamaulipas y el Valle de Texas.

Esta semana en "Frontera Grande: Descubrimiento Semanal" suenan:
{TRACK_1} — {ARTIST_1}
{TRACK_2} — {ARTIST_2}
{TRACK_3} — {ARTIST_3}
... y {N} temas más.

🎧 Escucha y sigue la playlist:
https://open.spotify.com/playlist/49qIAMVwZCHs5wLo1GLrlz

La rotación cambia cada lunes. ¿Tu proyecto ya tiene Spotify?
Regístralo en fronteragrande.mx y puede rotar la próxima semana.

#FronteraGrande #EscenaLocal #DescubrimientoSemanal
```

**Variables a rellenar cada lunes (salida del script):**
- `{TRACK_1}`, `{ARTIST_1}` … = tracks/artistas seleccionados esa semana
- `{N}` = total tracks en la playlist (default 24)

**Opcional (curación manual):** elegir 1 "Track de la semana" y añadir línea:
`⭐ Track de la semana: {TRACK_DESTACADO} — {ARTISTA_DESTACADO}`

---

### #3 — Para los fans (vie 28 ago 2026)

**Instagram:**

```text
¿Ya conoces TODA la escena de tu frontera? 🎵

En fronteragrande.mx tienes el directorio completo: bandas, DJ's y
solistas de Reynosa a Brownsville, filtrados por género y ciudad.
Gratis, sin registro y sin algoritmo que decida qué ves.

✅ Feed con posts y videos de tus artistas
✅ Agenda de toquines actualizada
✅ Playlist semanal nueva cada lunes en Spotify
✅ Avisos directos al celular cuando tu artista publica

¿Cómo tenerla en tu bolsillo?
📱 Abre fronteragrande.mx en Chrome o Safari
➕ Agrégala a pantalla de inicio
🔔 Activa las notificaciones

Gratis · Sin tiendas de apps · Tú mandas

👉 Link en bio

#FronteraGrande #EscenaLocal #MusicaIndependiente #Tamaulipas
#ValleDeTexas #Reynosa #Matamoros #NuevoLaredo #McAllen #Brownsville
```

**Facebook:**

```text
¿Ya conoces toda la escena musical de la frontera norte de Tamaulipas
y el Valle de Texas?

En fronteragrande.mx está todo: directorio por género y ciudad, feed
con lo que publican tus artistas, agenda de eventos, y cada lunes una
playlist nueva en Spotify con música 100% de la escena.

Lo mejor: te avisan directo al celular cuando tu artista publica o
anuncia toquín. Sin algoritmo de por medio.

¿Cómo instalarla?
• Android: ábrela en Chrome → menú → Agregar a pantalla de inicio
• iPhone: ábrela en Safari → botón Compartir → Agregar a inicio
• Activa las notificaciones

Gratis, sin App Store ni Play Store, y tú decides qué ves.

#FronteraGrande #EscenaLocal
```
