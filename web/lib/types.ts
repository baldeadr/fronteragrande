export interface LinkPrincipal {
  plataforma: string;
  url: string;
}

export interface Followers {
  ig: number | null;
  fb: number | null;
  yt: number | null;
  spotify: number | null;
  tt: number | null;
  beatport?: number | null;
  mixcloud?: number | null;
}

export interface StatsPlataforma {
  seguidores?: number | null;
  vistas?: number | null;
  reproducciones?: number | null;
  oyentes_mensuales?: number | null;
  fecha_captura?: string | null;
}

export type StatsPerfil = Record<string, StatsPlataforma>;

export interface Ranking {
  indice: number | null;
  audiencia: number | null;
  consumo: number | null;
  rank: number | null;
  total: number;
}

export interface AnalisisPerfil {
  texto: string;
  tipo: string;
  confianza: "alta" | "media" | "baja";
  actualizado: string | null;
}

export interface ConsumoAnalisis {
  patron: string;
  texto: string;
  balance: string;
  audiencia: {
    patron: string;
    dominancia: Record<string, number>;
  };
  consumo: {
    patron: string;
    dominancia: Record<string, number>;
  };
  ratios: {
    viralidad_yt: number | null;
    engagement_spotify: number | null;
    gap_social_musica: number | null;
  };
  dominancia: Record<string, number>;
}

export interface ArtistCard {
  slug: string;
  nombre: string;
  segmento: string;
  nivel: string;
  catalogado: boolean;
  ciudad: string;
  generos: string[];
  estado_activo: string;
  color_estado: string;
  metodo_actividad: string;
  verificado: boolean;
  ultimo_lanzamiento: string | null;
  ultimo_evento: string | null;
  followers: Followers;
  ranking: Ranking;
  menciones: string[];
  imagen_perfil: string | null;
  imagen_origen: string | null;
  link_principal: LinkPrincipal | null;
  links: LinkPrincipal[];
}

export interface Preview {
  tipo: "youtube" | "tiktok" | "instagram" | "facebook" | "spotify" | "soundcloud" | "mixcloud" | "imagen" | "texto";
  video_id?: string;
  embed_url?: string;
  thumbnail?: string;
  title?: string;
  author?: string;
}

export interface FeedItem {
  fecha: string | null;
  tipo: string;
  tipo_bruto?: string;
  fuente: string;
  titulo: string;
  url: string | null;
  detalle: string;
  artista: string;
  artista_slug: string | null;
  imagen_artista: string | null;
  nivel?: string;
  preview: Preview;
}

export interface Evento {
  id: number;
  nombre: string;
  fecha: string | null;
  lugar: string;
  ciudad: string;
  artistas: string;
  que_demuestra: string;
  fuente: string;
}

export interface SerieMes {
  mes: string;
  año: number;
  conteo: number;
}

export interface CiudadActividad {
  nombre: string;
  total: number;
  activo: number;
  en_duda: number;
  inactivo: number;
}

export interface EventoProximo {
  nombre: string;
  ciudad: string | null;
  fecha: string | null;
}

export interface Stats {
  total: number;
  verificados: number;
  generos: Record<string, number>;
  estados: Record<string, number>;
  estados_registro: Record<string, number>;
  ciudades: Record<string, number>;
  segmentos: Record<string, number>;
  feed_serie: SerieMes[];
  altas_por_mes: SerieMes[];
  seguidores: Record<string, number>;
  reproducciones: Record<string, number>;
  cobertura: Record<string, number>;
  posts_90dias: number;
  por_ciudad: CiudadActividad[];
  eventos_proximos: { total: number; ciudad: string | null; proximos: EventoProximo[] };
  ligas: {
    total: number;
    por_nivel: Record<string, number>;
    por_segmento: Record<string, number>;
    por_ciudad: Record<string, number>;
  };
  rookies: {
    total: number;
    por_segmento: Record<string, number>;
    por_ciudad: Record<string, number>;
    por_estado_activo: Record<string, number>;
  };
}

export interface LinkRed {
  plataforma: string;
  url: string;
  es_busqueda: boolean;
  nota: string;
  canal?: boolean;
  embebible?: boolean;
}

export interface EventoArtista {
  fecha: string | null;
  nombre: string;
  lugar: string;
  ciudad: string;
  artistas: string;
  que_demuestra: string;
}

export interface EstadoIgfb {
  configurado: boolean;
  conectado: boolean;
  pagina_fb: string | null;
  ig: string | null;
}

export interface EstadoTiktok {
  configurado: boolean;
  conectado: boolean;
  user_id: string | null;
}

export interface ArtistDetail {
  slug: string;
  nombre: string;
  segmento: string;
  nivel: string;
  catalogado: boolean;
  ciudad: string;
  generos: string[];
  es_propio: boolean;
  estado_activo: string;
  color_estado: string;
  metodo_actividad: string;
  estado_registro: string;
  verificado: boolean;
  ultimo_lanzamiento: string | null;
  ultimo_evento: string | null;
  followers: Record<string, number | null>;
  stats: StatsPerfil;
  fecha_captura: string | null;
  ranking: Ranking;
  menciones: string[];
  analisis: AnalisisPerfil;
  consumo: ConsumoAnalisis;
  igfb: EstadoIgfb;
  tiktok: EstadoTiktok;
  imagen_perfil: string | null;
  imagen_origen: string | null;
  logros: string;
  bio: string;
  notas: string;
  links: LinkRed[];
  eventos: EventoArtista[];
  feed: FeedItem[];
}

export interface RedForm {
  plataforma: string;
  url: string;
}

export interface OnboardingResult {
  imagen: string | null;
  videos: number;
  estado: string;
}

export interface ResultadoAlta {
  slug: string;
  nombre: string;
  onboarding: OnboardingResult;
}

export interface LinkAdmin {
  plataforma: string;
  url: string;
}

export interface AdminArtist {
  slug: string;
  nombre: string;
  segmento: string;
  nivel: string;
  es_leyenda: boolean;
  ciudad: string;
  generos: string;
  estado_activo: string;
  estado_registro: string;
  es_propio: boolean;
  bio: string;
  notas: string;
  logros: string;
  imagen_perfil: string | null;
  imagen_candidatas?: Record<string, string>;
  verificado: boolean;
  links: LinkAdmin[];
}

export interface ArtistaPendiente {
  slug: string;
  nombre: string;
  segmento: string;
  ciudad: string;
  fecha_registro: string | null;
  dias_sin_verificar: number;
  links: LinkAdmin[];
}
