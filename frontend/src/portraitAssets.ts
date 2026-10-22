import catalog from "./portrait-catalog.json";
import type { Driver } from "./types";
export interface PortraitAsset {
  name: string;
  src: string;
  author: string;
  license: string;
  licenseUrl: string;
  source: string;
  originalUrl: string;
  photoYear: number;
  position: string;
  changes: string;
}
export const PORTRAITS: PortraitAsset[] = catalog;
export function portraitKey(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z]/g, "");
}
const byName = new Map(PORTRAITS.map((p) => [portraitKey(p.name), p]));
const aliases: Record<string, string> = {
  alexalbon: "alexanderalbon",
  zhouguanyu: "guanyuzhou",
  carlossainzjr: "carlossainz",
  nicohuelkenberg: "nicohulkenberg",
  kimiantonelli: "andreakimiantonelli",
};
export function portraitFor(
  driver: Pick<Driver, "name" | "first_name" | "last_name">,
): PortraitAsset | null {
  for (const name of [
    driver.name,
    `${driver.first_name} ${driver.last_name}`,
  ]) {
    const key = portraitKey(name),
      asset = byName.get(aliases[key] || key);
    if (asset) return asset;
  }
  return null;
}
