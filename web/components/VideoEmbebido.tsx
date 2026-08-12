import type { FeedItem } from "@/lib/types";
import { fechaCorta } from "@/lib/formato";

export default function VideoEmbebido({ item }: { item: FeedItem }) {
  if (item.preview.tipo !== "youtube" || !item.preview.embed_url) return null;
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface">
      <iframe
        src={item.preview.embed_url}
        title={item.titulo}
        className="aspect-video w-full"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
      <div className="flex flex-col gap-1 px-3 py-2 text-sm">
        <p className="line-clamp-1 font-medium">{item.titulo}</p>
        <p className="text-xs text-muted">{fechaCorta(item.fecha)}</p>
      </div>
    </div>
  );
}