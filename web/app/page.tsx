import { api } from "@/lib/api";
import FeedLista from "@/components/FeedLista";
import HeroActividad from "@/components/HeroActividad";

export default async function Home() {
  const [stats, feed] = await Promise.all([api.stats(), api.feed()]);

  return (
    <div className="flex flex-col gap-6">
      <HeroActividad stats={stats} />
      <FeedLista items={feed} />
    </div>
  );
}
