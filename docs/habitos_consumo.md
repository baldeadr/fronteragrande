# Hábitos de consumo — Frontera Grande

 Marco conceptual para entender **cómo** la audiencia consume contenido
musical en la frontera grande de Tamaulipas, y cómo esa información
mejora el análisis por artista y las decisiones de producto.

---

## 1. Por qué importa

Un artista con 500K vistas en YouTube y 5K streams en Spotify no es
"mejor" o "peor" que uno con 20K oyentes mensuales y bajo perfil de
YouTube. Son **patrones de consumo distintos** que reflejan:

- **Hábitos de la audiencia regional**: en México y Latinoamérica,
  YouTube es la plataforma #1 para música, no Spotify. La audiencia
  busca y escucha donde puede sin pagar.
- **Tipo de contenido**: los videos de "audio" (imagen estática +
  canción) generan vistas que no equivalen a streams activos en
  Spotify. Son consumo pasivo, no descubrimiento intencional.
- **Monetización real**: YouTube paga por adsense (muy bajo para
  contenido de audio estático); Spotify paga por stream. Un artista
  con YouTube-dominante puede tener más alcance pero menos ingresos.
- **Descubrimiento vs. hábito**: la audiencia que busca "artista +
  canción" en YouTube tiene un hábito diferente a la que guarda
  playlists en Spotify.

Documentar estos patrones permite:
- Comparaciones más justas entre artistas de diferentes géneros.
- Análisis de valor para patrocinadores (alcance real vs. monetización).
- Mejores recomendaciones de playlist y contenido.
- Detectar oportunidades de crecimiento por plataforma.

---

## 2. Patrones de dominancia por plataforma

### 2.1 YouTube-dominante

**Señal:** vistas YT >> streams Spotify, ratio vistas/suscriptores alto.

**Qué significa:**
- La audiencia busca y escucha gratis en YouTube.
- El contenido audio/video es su vía principal de consumo.
- Puede haber viralidad (videos que se comparten y se escuchan
  repetidamente sin seguir al artista).
- Común en artistas regionales,bandas en vivo y covers.

**Implicaciones:**
- Alto alcance potencial, baja monetización directa.
- Oportunidad: convertir vistas en seguidores de Spotify (calls to
  action en descripciones, cards, end screens).
- El ranking puede sobrestimar el "éxito" si solo mira vistas.

### 2.2 Spotify-dominante

**Señal:** oyentes mensuales >> vistas YT, followers Spotify significativos.

**Qué significa:**
- La audiencia descubre y guarda en playlists.
- Consumo más "intencional": el oyente elige escuchar, no solo busca.
- Común en artistas indie, solistas, proyectos con presencia en
  playlists curadas.

**Implicaciones:**
- Mejor monetización por stream.
- Oportunidad: fortalecer redes sociales para ampliar descubrimiento.
- El ranking puede subestimar artistas con bajo perfil social pero
  alta reproducción en streaming.

### 2.3 Social-dominante

**Señal:** seguidores IG/FB/TT significativos, sin métricas musicales.

**Qué significa:**
- La audiencia ve contenido pero no escucha en plataformas musicales.
- Puede ser un artista con buen contenido visual/marketing pero sin
  distribución en streaming.
- Común en DJs, colectivos y proyectos de events.

**Implicaciones:**
- Oportunidad clara: conectar con plataformas musicales.
- El ranking lo penaliza porque no hay consumo musical registrado.

### 2.4 Distribuido

**Señal:** presencia equilibrada en 3+ plataformas sin dominancia clara.

**Qué significa:**
- Audiencia multicanal; consume donde está conveniente.
- Proyecto con estrategia activa en múltiples plataformas.

**Implicaciones:**
- Ideal para patrocinadores (alcance diversificado).
- Ranking favorable pero no exceptional en ningún aspecto.

---

## 3. Métricas derivadas (sin datos nuevos)

Con los campos ya existentes en la BD (`artists` + `feed_items`), se
pueden calcular las siguientes métricas sin recolectar información
adicional.

### 3.1 YouTube viralidad

```
ratio_viralidad_yt = vistas_yt / followers_yt
```

- **>10**: el contenido se viraliza; la audiencia escucha pero no
  sigue al canal.
- **1-10**: comportamiento normal; la audiencia sigue y consume.
- **<1**: bajo engagement; el canal no genera vistas significativas.

### 3.2 Spotify engagement

```
ratio_engagement_spotify = oyentes_mensuales / followers_spotify
```

- **>1**: la audiencia que escucha supera a los que siguen; hay
  descubrimiento activo (playlists, recomendaciones).
- **<1**: los seguidores son fieles pero la audiencia pasiva es baja.
- **0**: no hay datos (modo desarrollo o sin Extended Quota).

### 3.3 Gap social→música

```
ratio_social_musica = (IG + FB + TT + YT followers) /
                      (Spotify listeners + Bandcamp plays + SoundCloud plays)
```

- **>10**: la audiencia social es mucho mayor que la musical; hay
  oportunidad de conversión.
- **1-10**: distribución razonable.
- **<1**: la audiencia musical supera la social; el artista es
  "descubrible" pero no "seguible".

### 3.4 Dominancia por dimensión (audiencia vs. consumo)

Para que la comparativa sea justa, ya **no** se mezclan unidades
incomparables en una sola cifra (históricamente las vistas de YouTube,
enormes por naturaleza, sepultaban a los seguidores sociales o a los
oyentes de Spotify). Ahora se analizan dos dimensiones por separado,
cada una comparando solo unidades equivalentes en escala `log10`:

```
dominancia_audiencia = reparto de seguidores (IG/FB/TT/YT/Spotify/Beatport/Mixcloud) en escala log
dominancia_consumo   = reparto de reproducciones/vistas (YT/Spotify/Bandcamp/SoundCloud) en escala log
patron               = plataforma dominante de la dimensión, o "distribuido"
```

Cada dimensión produce su propio patrón (p. ej. "Instagram-dominante"
en audiencia y "YouTube-dominante" en consumo), y una lectura global
(`balance_audiencia_consumo`) compara ambas: consumo≫audiencia
(consumo_dominante), equilibrio, o audiencia≫consumo (social_dominante).

Implementación:

- `lib/helpers.py`: `dominancia_audiencia()`, `dominancia_consumo()`,
  `balance_audiencia_consumo()`, `_share_log()`.
- `lib/servicios.py` → `analisis_consumo()` devuelve `{audiencia,
  consumo, balance, texto, ratios}` en lugar de una dominancia única.

### 3.5 Benchmark por género

```
promedio_genero = media(metricas) WHERE genero = X
diferencia_genero = (metricas_artista - promedio_genero) / promedio_genero * 100
```

Cómo se compara un artista con el promedio de su género. Un artista
con 50K vistas YT puede ser exceptional en un género niche pero
promedio en otro.

### 3.6 Frecuencia de publicación

A partir de `feed_items` con `fecha` y `fuente`:

- **Posts por mes por plataforma**: qué tan activo es el artista en
  cada red.
- **Consistencia**: desviación estándar de intervalos entre posts
  (regular vs. intermitente).
- **Plataforma descuidada**: time since last post por plataforma.

---

## 4. Cómo mejora el análisis actual

### 4.1 Análisis por artista (perfil)

**Hoy:** `analisis_artista()` en `lib/servicios.py` devuelve un texto
genérico en 5 categorías (datos_insuficientes, presencia_social,
puente_musical, descubrimiento, presencia_distribuida).

**Propuesto:** enriquecer con:
- **Patrón detectado**: YouTube-dominante, Spotify-dominante,
  Social-dominante, Distribuido.
- **Ratios clave**: viralidad YT, engagement Spotify, gap social→música.
- **Benchmark**: cómo se compara con artistas de su género/ciudad.
- **Oportunidad sugerida**: "Fortalecer Spotify" / "Activar redes" /
  "Mantener equilibrio".

### 4.2 Ranking de alcance

**Hoy:** el ranking separa audiencia (55%) de consumo (45%) pero no
captura la calidad del consumo.

**Propuesto:** considerar:
- El **tipo de consumo** (vistas pasivas vs. streams activos) puede
  ajustar el peso de YouTube en el ranking.
- Un artista con YouTube-dominante puede tener un ranking alto por
  vistas, pero su monetización real es baja. Esto es relevante para
  comparaciones con patrocinadores.

### 4.3 Stats de la escena

**Hoy:** gráficas de actividad temporal, ranking por red, ecosistema
de redes.

**Propuesto:** agregar:
- **Distribución de dominancia**: qué % de artistas son
  YouTube-dominantes vs. Spotify-dominantes.
- **Gap promedio social→música**: la escena convierte seguidores en
  oyentes?
- **Benchmark por género**: qué géneros tienen mejor engagement en
  Spotify.

---

## 5. Implementación

### 5.1 Documentación

| Archivo | Acción |
|---------|--------|
| `docs/habitos_consumo.md` | Este documento (marco conceptual). |
| `docs/datos_automaticos.md` | Actualizar tabla de datos derivados con las métricas de consumo. |
| `docs/vision.md` | Agregar referencia a este documento en la sección de análisis. |

### 5.2 Backend

| Archivo | Acción |
|---------|--------|
| `lib/helpers.py` | Funciones puras: `ratio_viralidad_yt()`, `ratio_engagement_spotify()`, `dominancia_audiencia()`, `dominancia_consumo()`, `balance_audiencia_consumo()`. |
| `lib/servicios.py` | Enriquecer `analisis_artista()` con patrón detectado + ratios + benchmark; `analisis_consumo()` separa audiencia y consumo. |
| `backend/main.py` | Agregar campo `consumo` al endpoint de detalle de artista. |

### 5.3 Frontend

| Archivo | Acción |
|---------|--------|
| `web/components/` | Nuevo componente `ConsumoAnalisis.tsx` para perfil de artista. |
| `web/components/stats/` | Nuevo componente `ConsumoEscena.tsx` para gráficas de escena. |
| `web/app/artistas/[slug]/page.tsx` | Integrar componente de consumo en el perfil. |

### 5.4 Datos

| Archivo | Acción |
|---------|--------|
| `scripts/` | Script puntual para calcular métricas derivadas de todos los artistas existentes. |
| `lib/repository.py` | Agregar consultas para benchmarks por género/ciudad si se necesitan. |

---

## 6. Limitaciones y consideraciones

- **Sin datos nuevos:** todo se calcula a partir de campos existentes.
  No se requiere接入 APIs adicionales.
- **YouTube "audio" no equivale a Spotify stream:** un view en YouTube
  no es un play en Spotify. Las métricas son comparables dentro de su
  propia plataforma, no entre plataformas.
- **Regional bias:** en la frontera grande, YouTube domina por hábito.
  Un artista con YouTube-dominante no es "peor" que uno con
  Spotify-dominante; simplemente refleja el mercado.
- **Sin Extended Quota:** mientras Spotify no entregue
  followers/popularity, las métricas de Spotify serán limitadas. Esto
  afecta los benchmarks y los ratios.
- **No inventar datos:** todas las métricas derivadas usan datos con
  fuente (CSV semilla, APIs conectadas, scraping verificado).

---

Última actualización: 2026-08-26.
