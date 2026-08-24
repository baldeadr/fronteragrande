# Finanzas y monetización — Frontera Grande

Análisis inicial para sostener económicamente el sitio sin convertir la
monetización en el objetivo del proyecto. Este documento separa datos
verificados, supuestos y decisiones pendientes.

## 1. Alcance económico real

Frontera Grande no busca captar a todo el público de la frontera grande de
Tamaulipas. Su audiencia es de nicho:

- Artistas y proyectos musicales.
- Seguidores de la escena local.
- Foros, bares y promotores.
- Fotógrafos, productores y técnicos.
- Escuelas y tiendas de instrumentos.
- Medios culturales y organizadores.

La oportunidad no está en alcanzar grandes volúmenes de tráfico general, sino
en concentrar una audiencia local con alta afinidad musical. Para un negocio de
la escena, una visita relevante puede tener más valor que muchas visitas sin
relación con su actividad.

## 2. Costos actuales

| Servicio | Uso | Costo actual |
|---|---|---:|
| Vercel | Web Next.js | $0 |
| Render | API FastAPI | $0* |
| Neon | PostgreSQL | $0* |
| GitHub Actions | Sincronización Meta | $0 dentro del uso disponible |
| UptimeRobot | Monitor de salud | $0 en el plan gratuito |
| Dominio `fronteragrande.mx` | Identidad pública | $30.70 USD por un año; vence 2027-08-20 |
| AdSense | Monetización | Sin costo fijo de alta |

\* Los niveles gratuitos tienen límites de uso, almacenamiento, suspensión o
disponibilidad. El costo real puede cambiar cuando el tráfico o la operación
superen esos límites.

La infraestructura actual puede mantenerse casi gratis. Antes de contratar
servicios de datos, debe medirse la audiencia real.

### Costo anual con app en tiendas (condicional)

Si el sitio se publica como app en tiendas (roadmap, etapa 23), los costos
adicionales serían:

| Concepto | Costo |
|---|---:|
| Google Play (cuenta de desarrollador) | $25 USD una sola vez |
| Apple Developer Program | $99 USD por año |
| Dominio `fronteragrande.mx` | $30.70 USD por año |

Primer año con ambas tiendas: **~$154.70 USD**. Años siguientes:
**~$129.70 USD**.

Condición acordada con el artista: publicar en tiendas **solo cuando el
ingreso anual del sitio cubra el costo anual recurrente (~$130 USD)**,
medible con AdSense + patrocinios tras los 90 días de audiencia.

## 3. Plataformas de datos musicales

Los precios son referencias observadas en las páginas oficiales durante agosto
de 2026 y pueden cambiar. Un plan de dashboard no equivale necesariamente a
una licencia para importar y redistribuir datos desde una aplicación propia.

| Plataforma | Dashboard publicado | API publicada | Cobertura relevante |
|---|---:|---:|---|
| Soundcharts | Desde $10/mes para 1 artista; $49/mes para 10; $129/mes Pro | Desde $250/mes | Spotify, Apple Music, YouTube, TikTok, Instagram, Facebook, X, SoundCloud, Deezer, radio y playlists |
| Chartmetric | Desde $40/mes para 10 artistas; $117/mes Premium | Desde $350/mes | Spotify, Apple Music, YouTube, TikTok, Instagram, playlists, radio y charts |
| Viberate | $39.90/mes o $239/año; prueba de 2 días sin tarjeta | API mediante cotización | Spotify, Apple Music, YouTube, TikTok, Instagram, Facebook, SoundCloud, Deezer, Beatport, Shazam, radio y playlists |
| Songstats | Precio de API no transparente para este uso | No confirmado | Seguimiento de cuentas y lanzamientos conectados por el artista |

Los datos de estas plataformas son agregados, estimados o derivados de varias
fuentes. Si se incorporan, deben mostrarse con proveedor y fecha de captura; no
deben presentarse automáticamente como cifras oficiales entregadas por
Spotify.

Fuentes de precios y cobertura:

- [Soundcharts — precios](https://soundcharts.com/en/pricing)
- [Soundcharts — API](https://developers.soundcharts.com/api/getting-started)
- [Chartmetric — precios](https://chartmetric.com/pricing)
- [Viberate — precios](https://www.viberate.com/pricing/)

## 4. Publicidad

### AdSense

AdSense no publica un RPM garantizado por país o nicho. Por eso no se debe
proyectar el ingreso usando una cifra de mercado como si fuera un hecho.

Fórmula cuando exista medición real:

```text
RPM observado = ingresos / vistas monetizadas × 1,000
ingreso estimado = vistas monetizadas / 1,000 × RPM observado
```

Escenarios internos únicamente ilustrativos:

| Vistas mensuales | RPM supuesto $1 | RPM supuesto $3 | RPM supuesto $5 |
|---:|---:|---:|---:|
| 10,000 | $10 | $30 | $50 |
| 25,000 | $25 | $75 | $125 |
| 50,000 | $50 | $150 | $250 |
| 100,000 | $100 | $300 | $500 |

Estos valores son supuestos de sensibilidad, no una predicción de ingresos.

AdSense requiere contenido original, navegación clara y cumplimiento de las
políticas de editores. Está prohibido generar clics propios, incentivar clics,
comprar tráfico de baja calidad o hacer que los anuncios parezcan botones de
reproducción o enlaces editoriales.

Fuentes:

- [Elegibilidad de AdSense](https://support.google.com/adsense/answer/9724)
- [Políticas de AdSense](https://support.google.com/adsense/answer/48182)
- [Tráfico no válido](https://support.google.com/adsense/answer/16737)

### Patrocinios directos

Para una audiencia local y especializada, los patrocinios son más prometedores
que depender exclusivamente de AdSense. Posibles anunciantes:

- Foros, bares y restaurantes con música en vivo.
- Escuelas de música y estudios de grabación.
- Tiendas de instrumentos, audio e iluminación.
- Productores y promotores.
- Fotógrafos, videógrafos y diseñadores.
- Universidades y espacios culturales.
- Marcas locales relacionadas con entretenimiento.

El valor comercial debe demostrarse con datos reales:

- Usuarios y sesiones de la zona.
- Visitas a perfiles y eventos.
- Clics hacia redes, mapas, WhatsApp o boletos.
- Usuarios recurrentes.
- Afinidad por ciudad, categoría o género.
- Clics y conversiones del patrocinador.

No se debe prometer alcance masivo. El argumento principal es la relevancia
local:

> Frontera Grande conecta tu negocio con personas que ya están interesadas en
> la escena musical local.

## 5. Afiliados y eventos

Se pueden explorar acuerdos con organizadores mediante:

- Comisión por boleto atribuido.
- Código promocional exclusivo.
- Enlace con parámetros UTM.
- Pago por lead o contacto.
- Patrocinio de la cartelera.

No debe asumirse que una boletera ofrece afiliados hasta tener un acuerdo
confirmado. La comisión, atribución, cancelaciones y devoluciones deben quedar
por escrito.

## 6. Punto de equilibrio

Definición general:

```text
Costo mensual total = infraestructura + dominio + servicios + operación + impuestos
Ingreso total = publicidad + patrocinios + afiliados + otros ingresos
Punto de equilibrio cuando ingreso total >= costo mensual total
```

Sensibilidad de vistas necesarias usando los RPM supuestos anteriores:

| Costo mensual | RPM $1 | RPM $3 | RPM $5 |
|---:|---:|---:|---:|
| $40 | 40,000 | 13,334 | 8,000 |
| $70 | 70,000 | 23,334 | 14,000 |
| $250 | 250,000 | 83,334 | 50,000 |
| $350 | 350,000 | 116,667 | 70,000 |

La tabla muestra por qué no conviene contratar una API de $250 o $350 al mes
solo con la expectativa de cubrirla mediante anuncios de una audiencia local.

## 7. Estrategia recomendada

1. Mantener Vercel, Render y Neon en el nivel gratuito.
2. Registrar el dominio cuando la audiencia esté validada.
3. Medir audiencia durante 90 días antes de fijar tarifas.
4. Medir perfiles, eventos, clics a redes, mapas, WhatsApp y patrocinadores.
5. Probar un patrocinio local directo antes de contratar una API premium.
6. Activar AdSense como ingreso complementario, no como fuente principal.
7. No contratar una API de datos hasta que exista ingreso recurrente que cubra al menos el doble de su costo.
8. Separar visualmente publicidad, patrocinio y contenido editorial.
9. Entregar a patrocinadores datos agregados, nunca identificadores personales.

La secuencia financiera propuesta es:

```text
medir audiencia → conseguir patrocinio piloto → validar ingresos → contratar datos premium
```

## 8. Datos que faltan

- Usuarios, sesiones y vistas mensuales reales.
- Porcentaje de tráfico de la zona objetivo.
- Visitas recurrentes.
- Visitas a perfiles y eventos.
- Clics salientes por plataforma.
- Costo anual real del dominio.
- Plan exacto y límites de cualquier proveedor de datos.
- Primer patrocinador y tarifa negociada.
- Situación fiscal del titular.

Hasta obtener esos datos, cualquier cálculo de alcance o ingreso debe tratarse
como escenario y no como pronóstico.
