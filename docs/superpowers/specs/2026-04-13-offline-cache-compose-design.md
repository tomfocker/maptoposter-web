# Offline Cache Compose Design

Date: 2026-04-13
Project: MapToPoster Web
Status: Proposed and user-approved for planning

## Goal

Design an offline-cache packaging strategy that keeps the main Docker image slim, preloads commonly used China city map data to avoid first-run download latency, and still preserves normal online fallback behavior.

This design intentionally does not change the semantic meaning of the existing `dist` parameter in the rendering engine. Instead, it updates user-facing copy so the parameter is described as a map/poster view range control rather than a strict geographic radius.

## Product Decisions

- Keep the existing `dist` behavior from the original project and current fork.
- Do not redefine `dist` as a true physical radius.
- Update UI/README/help copy from "radius" wording to "map range" or "poster view range".
- Preserve online fallback by default.
- Add offline seed data for major China cities.
- Allow already-cached map data to be reused across size changes whenever the cached coverage is sufficient.

## Why Keep The Existing `dist` Semantics

The original `maptoposter` project already treats distance as a poster-composition parameter, not a strict GIS radius. The current fork inherits that logic. For this product, preserving the original behavior is preferable because:

- It matches the original tool's visual intent.
- It keeps the familiar distance guide:
  - `4000-6000`: small or dense city center
  - `8000-12000`: medium city or focused downtown
  - `15000-20000`: large metro or broader city view
- It avoids exploding offline package size by forcing true-radius coverage.
- It is sufficient for "beautiful city poster" output, which is more about composition than map completeness.

## Offline Packaging Strategy

Use a multi-image structure:

1. Application image: `maptoposter-web:latest`
2. Offline cache image: `maptoposter-cache:cn-major-v1`
3. Shared named volume: `map_cache`
4. Init container: `maptoposter-cache-init`

### Responsibilities

#### Application Image

- Contains app code, themes, fonts, and runtime dependencies.
- Does not include the heavy offline cache bundle.
- Reads and writes runtime cache from `/app/cache`.

#### Offline Cache Image

- Contains pre-generated cache files under a seed directory such as `/seed-cache`.
- Contains a cache index describing available city centers and coverage tiers.
- Does not run the application itself.

#### Named Volume

- Stores the runtime cache used by the main app.
- Receives seeded offline data on first startup.
- Persists later online-fetched data so users keep newly downloaded maps.

#### Init Container

- Runs before the app or alongside startup.
- If the named volume is empty, copies `/seed-cache/*` into `/app/cache`.
- If the named volume already contains cache data, it exits without overwriting user data.

## Default Runtime Behavior

The system is not "offline-only". It is "offline-seeded with online fallback".

Behavior:

- If a request is covered by an offline-seeded cache entry, render from local cache.
- If a request is not covered, fetch online from Nominatim/OSM/Overpass as today.
- Store newly downloaded results into the same named volume.
- Future requests can reuse those newer cached results.

This preserves normal online behavior while removing startup friction for common China-city poster requests.

## China Offline Seed Scope

### Base Tier

- About 70 major China cities.
- Seed the commonly useful `dist=10000` tier.

This tier is intended to cover the majority of "quality poster" requests centered on well-known cities.

### Extended Tier

Add a broader tier for 8 mega cities:

- Beijing
- Shanghai
- Guangzhou
- Shenzhen
- Chongqing
- Chengdu
- Wuhan
- Hangzhou

Seed an additional `dist=18000` tier for these cities.

This reduces fallback downloads for broader metropolitan views while keeping the package materially smaller than a "full large-radius for everything" strategy.

## Cache Reuse Across Size Changes

### Problem

Today the cache is effectively keyed by exact request parameters, especially the computed graph/features distance. That means a size change can lead to a different fetch radius and miss the cache even when an existing larger cached area already fully covers the request.

### Desired Behavior

Once a city has already been cached with enough geographic coverage, the app should reuse that cached map data even if:

- the poster size changes
- the aspect ratio changes
- the theme changes
- the new request is for a smaller effective coverage area
- the map shift is small enough to remain inside existing coverage

### Design

Store cache entries by geographic coverage, not only by raw request parameters.

Each reusable cache entry should include:

- normalized city-center coordinates
- cached data type (`graph`, `water`, `parks`)
- effective geographic coverage distance used for fetch
- optional metadata such as source city name and generation timestamp

Maintain a lightweight cache index file, for example:

- `/app/cache/index.json`

The index should map a normalized city center to available coverage tiers and file locations.

### Lookup Rule

At request time:

1. Resolve the city center.
2. Compute the effective fetch coverage needed for the current `dist`, poster size, and offsets.
3. Search the local cache index for the smallest cached entry whose coverage fully satisfies the request.
4. If found, reuse it.
5. If not found, fetch online and add a new index entry.

This allows:

- `dist=10000` seed data to serve smaller requests
- one cached city dataset to work across multiple poster sizes
- broader seeded data to reduce unnecessary network traffic

## Size Guidance

Because this design keeps the original `dist` semantics rather than converting them to strict real-radius coverage, the data package remains manageable.

Expected directionally:

- `cn-major-v1` should stay materially smaller than a true-radius 10 km nationwide package
- the base tier plus mega-city extended tier should remain practical for Docker distribution
- online fallback still covers uncommon sizes, offsets, and cities outside the seed list

The exact image size should be validated after generating the real seed dataset. A reasonable product goal is to keep the offline cache image in a range that is still practical for registry distribution and one-time download.

## Docker Compose Structure

Recommended composition:

- `maptoposter` service for the application
- `cache-init` one-shot service for seeding the named cache volume
- `map_cache` named volume for persistent shared cache

Behavioral requirements:

- The app service mounts `map_cache` at `/app/cache`
- The init service mounts both `map_cache` and the seed data source
- The init service must be idempotent
- The app must not bind-mount a host `./cache` path in offline mode because that would hide seeded image content and defeat the managed volume design

## User-Facing Compose Experience

The user should have a clean way to opt into offline acceleration without changing the core image structure.

Recommended distribution:

- Keep the default compose file focused on the normal slim app image
- Add an offline compose override for the China package

Suggested user flow:

- normal mode: `docker compose up -d`
- offline China mode: `docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml up -d`

This keeps the default setup simple while offering a standard opt-in path for users who want seeded local data.

## User-Facing Copy Changes

Update user-visible wording:

- Replace "render radius" or "radius (meters)" with "map range" or "poster view range"
- Keep the familiar distance guide bands
- Explain that larger values show broader city context
- Explain that cached maps can often be reused across different poster sizes

## Error Handling

- If the cache index is missing or corrupted, fall back to online fetch and rebuild entries incrementally.
- If the seed copy step fails, the application should still start and behave like the online-only mode.
- If an online request fails, existing behavior should remain: render only when sufficient data exists and surface helpful failure logs.

## Testing Strategy

Implementation should verify:

1. Seed volume population on empty cache volume
2. No overwrite on non-empty cache volume
3. Cache hit for same city and same tier
4. Cache hit when a larger cached coverage satisfies a smaller request
5. Cache reuse across size changes
6. Cache miss and online fetch when requested coverage exceeds seeded coverage
7. Cache index update after an online fetch
8. Offline override compose starts successfully

## Out Of Scope

- Full offline geocoding for arbitrary world cities
- Full China offline coverage for every city and every distance tier
- Turning the product into a strict offline GIS renderer
- Reworking theme/rendering aesthetics

## Implementation Notes

- The current caching layer will need to move from simple key-based pickle lookup toward metadata-aware lookup.
- The existing cache data can still be stored as pickles, but file naming should align with the new coverage/index model.
- The online fallback path should remain the default behavior when no suitable cached coverage exists.

## Recommended Next Step

Write an implementation plan that covers:

- cache index design
- cache lookup/refactor strategy
- offline seed packaging pipeline
- compose override wiring
- user-facing copy updates
