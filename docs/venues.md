# Venues y lugares de la escena `[PROPUESTA]`

Documento inicial para explorar la incorporación de los **establecimientos y
lugares donde se toca** a Frontera Grande. No representa una decisión aprobada
ni compromete todavía modelo de datos, ingesta ni alcance.

## Motivación

- **Historia cultural:** la escena musical no son solo los proyectos, sino los
  espacios donde se han hecho y se hacen realidad los toquines: bares, foros,
  teatros, plazas, salones de eventos, centros culturales, estudios abiertos.
  Documentar tanto los **activos** como los **históricos** (lugares que ya no
  existen o ya no reciben música) es parte del relato de la frontera grande.
- **Fuente de publicaciones de eventos:** los venues publican carteles y toquines
  de forma continua; hoy el campo `lugar` de `events` es texto libre. Normalizar
  el lugar como entidad propia permite citar, agrupar y sincronizar carteles que
  ahora se pierden o se repiten.
- **Patrocinadores potenciales:** los bares y espacios locales son el patrocinador
  natural de la escena (ver `docs/finanzas.md`). Una ficha de venue con datos de
  la escena que lo visita es un puente concreto hacia `patrocinios directos a
  locales de la zona` (roadmap, Fase 3).
- **Geografía de la escena:** cuando exista el mapa por origen (PostGIS), los
  venues son la capa de espacios que complementa a la de artistas.

## Qué es

- Un **registro documental público** de los lugares donde se toca o se tocó en la
  frontera grande: nombre, ciudad, tipo de espacio, estado (activo/histórico) y
  fuente.
- Un **complemento de eventos**: cada evento puede citar su venue en lugar de un
  texto libre, y cada venue puede listar sus eventos pasados/próximos.
- Un **mapa de espacios** (futuro): capa de venues sobre PostGIS, junto al mapa
  de artistas por origen.
- Con **status de señal propio**: cada venue indica si sigue activo (programa
  música) o es histórico/cerrado, con una regla de actividad escalada a espacios.

## Qué no es

- **No es boletería ni promoción comercial**: listar lugares es registro de la
  escena, no venta de boletos ni anuncios pagados (misma regla que `events`).
- **No es booking ni calificación**: Frontera Grande no agenda ni puntúa venues.
- **No inventa datos**: los lugares históricos y sus historias requieren fuente;
  lo que falta por confirmar se marca `[PENDIENTE]`.

## Perfil de venue y mezcla de contenido

`[PROPUESTA]` Diseño pensado para que la promoción del lugar no ensucie el feed.

- Cada venue tendría su **propia página** (su ficha), donde vive **todo su
  contenido**: publicaciones, carteles y publicidad de su propio espacio, sin
  mezclarse con nada más.
- Al **feed principal solo entran sus eventos** (toquines), igual que hoy entran
  los eventos de los artistas. La publicidad del venue no aparece en el feed.
- Fundamento: el feed es la **bitácora de actividad de la escena** (qué se toca y
  dónde), no un canal publicitario. La señal de vida de un espacio no son sus
  posts de promoción, sino los eventos que programa.
- `[PENDIENTE]` confirmar si la página del venue se autorregistra o solo es
  curaduría, y si necesita algún tipo de verificación (probablemente más ligera
  que la de artistas).

## Status de señal (¿sigue activo?)

`[PROPUESTA]` Reutilizar la regla de actividad de los artistas aplicada a
espacios, para que el registro no envejezca (los lugares cierran o cambian de
giro):

- **activo** = señal ≤ 6 meses · **en_duda** = señal entre 6 y 18 meses o sin
  señal · **inactivo** = sin señal en más de 18 meses o cierre confirmado
  (misma lógica que `scraper/core.py`).
- **Señal para un venue**: eventos/toquines publicados con fecha, actualización
  de su página y carteles recientes.
- Campos propios `estado_activo` + `ultimo_evento` (solo avanza), actualizados
  por los syncs y el recalculo de actividad, sin inventar datos.

## Mapa de venues

`[PROPUESTA]` Cuando exista el mapa por origen (PostGIS, etapa del roadmap), los
venues son la **capa de espacios**: puntos por ciudad que complementan la capa de
artistas. La geolocalización (`lat`/`lon`) del modelo de datos lo habilita desde
el registro.

## Alcance propuesto

Ciudades de la frontera grande (Tamaulipas + Valle del Río Grande), con el mismo
criterio de ciudad base única que los artistas. Incluye espacios **activos**
(abiertos y programando música) e **históricos** (cerrados, cambiados de giro o
sin actividad musical actual), siempre con fuente.

## Modelo de datos propuesto `[PENDIENTE]`

| Campo | Nota |
|---|---|
| `nombre` | Nombre del lugar |
| `ciudad` | Ciudad base única (mismo dropdown que artistas) |
| `tipo` | `[PENDIENTE]` categorizar: bar, foro, teatro, plaza, salón de eventos, centro cultural, estudio, gimnasio/otro |
| `estado` | `[PENDIENTE]` activo / histórico / cerrado (definir taxonomía) |
| `lat` / `lon` | Geoposición para la futura capa de mapa (PostGIS) |
| `enlaces` | Página/redes del lugar (mismo patrón que `artist_links`) |
| `notas` | Historia, fuente y contexto cultural |
| `estado_activo` | Señal de actividad (activo / en_duda / inactivo), regla de actividad escalada a espacios |
| `ultimo_evento` | Fecha del último toquín/evento publicado (señal, solo avanza) |
| `es_propio` | Si el lugar es del propio universo (`architecting-a-band`) |

**Relación con eventos:** `events.lugar` es hoy texto libre; se propone un
`venue_id` opcional (FK) para citar el venue sin romper los eventos existentes.

## Fuente de publicaciones de eventos

- Hoy la ingesta de eventos viene de las páginas Meta de los artistas
  (`pagina_eventos`). Extensión lógica: sincronizar también las páginas de los
  venues (con su autorización) o por curaduría del proyecto.
- Los carteles de toquines publicados en redes de venues pueden nutrir la
  sección de eventos y el feed, con anti-duplicados por URL (patrón existente).
- **Dependencia:** esta fase depende de que la app de Meta quede aprobada en su
  revisión (`[PENDIENTE]`, en revisión) y de que cada venue autorice su página.

## Puente hacia patrocinadores

- La **aspiración de profesionalización** de `docs/vision.md` ya menciona venues,
  promotores y marcas. Una ficha pública de venue muestra a un patrocinador local
  el tipo de público que visita su espacio (datos de la escena agregados por
  ciudad/género), sin inventar métricas.
- Fase posterior: portafolio de patrocinio (paquete de visibilidad) como parte de
  la monetización (AdSense/patrocinios), ver `docs/finanzas.md`.

## Plan de implementación sugerido

1. **Definir** `[PENDIENTE]` la taxonomía de tipos y estados + modelo de datos +
   migración ligera (`db/database.py`).
2. **Seed inicial** con lugares actuales e históricos con fuente (investigación/
   curaduría; regla: no inventar).
3. **Página pública** de venues (ficha con su contenido/publicidad, **aislada**
   del feed) + enlace desde eventos (`lugar` ligado a venue); al feed principal
   solo entran los **eventos**.
4. **Status de señal**: `estado_activo` + `ultimo_evento` con la regla de
   actividad escalada a espacios (`scraper/core.py`).
5. **Mapa**: capa de venues (PostGIS) junto al mapa de artistas.
6. **Sync de carteles** de venues (Meta con autorización del dueño, tras la
   revisión de la app) — fase avanzada.
7. **Monetización**: portafolio de patrocinio local — fase monetización.

## Decisiones pendientes `[PENDIENTE]`

- Taxonomía de **tipo** de espacio y de **estado** (activo/histórico/cerrado).
- **Señal de actividad**: confirmar la definición de señal para venues y umbrales
  (propuesta: misma regla que artistas, señal = toquines/eventos publicados).
- **Mezcla de contenido**: confirmar el diseño de página propia del venue + solo
  eventos al feed principal (propuesta arriba).
- **Mapa de venues**: confirmar que es parte de la etapa del mapa (PostGIS).
- ¿Los venues se **registran ellos mismos** (como los artistas) o solo curaduría
  del proyecto?
- ¿Campos de **contacto** públicos (teléfono, reservas)? ¿Aforo y días de música?
- ¿Ranking de venues (afinidad por género/ciudad) o solo directorio?
- Cuál es la línea entre registro documental y publicidad comercial.
- Dependencia externa: revisión del **registro de Meta** (en revisión) para el
  sync de carteles de venues.