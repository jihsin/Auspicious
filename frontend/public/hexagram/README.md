# 卦象 Trigram Imagery

Each of the 8 trigrams has a placeholder SVG used as Layer 1 thumbnail in DivinationDrawer.

| File              | Trigram | Element |
|-------------------|---------|---------|
| heaven.svg        | 乾 ☰    | 天 sky |
| earth.svg         | 坤 ☷    | 地 earth |
| water.svg         | 坎 ☵    | 水 water |
| wind.svg          | 巽 ☴    | 風 wind |
| thunder.svg       | 震 ☳    | 雷 thunder |
| fire.svg          | 離 ☲    | 火 fire |
| lake.svg          | 兌 ☱    | 澤 lake |
| mountain.svg      | 艮 ☶    | 山 mountain |

## Replacing with real photos

These SVG placeholders are intentionally minimal. To upgrade:

1. Find a CC0/CC-BY photo on Unsplash matching the element (search e.g. "open sky", "still lake")
2. Crop/resize to 800×800 (square, 2x retina)
3. Save as JPG at the same filename (e.g., `heaven.jpg`)
4. Update `frontend/src/components/DayInsightCard/divination/imagery.ts` — change `src` from `.svg` to `.jpg`

The CSS gradient fallback in `imagery.ts` matches each trigram's tonal palette and renders if the image fails to load.

## Suggested Unsplash searches per trigram

- 乾 heaven: "blue sky cumulus", "sunlit horizon"
- 坤 earth: "rolling field", "soft farmland"
- 坎 water: "river current", "rain falling"
- 巽 wind: "windswept grass", "tall reeds"
- 震 thunder: "lightning storm", "dramatic cloud"
- 離 fire: "campfire", "morning sun"
- 兌 lake: "calm lake at dusk", "still water reflection"
- 艮 mountain: "mountain ridge", "alpine peak"
