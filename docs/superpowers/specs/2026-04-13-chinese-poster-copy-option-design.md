# Chinese Poster Copy Option Design

Date: 2026-04-13
Project: MapToPoster Web
Status: Proposed and user-approved for planning

## Goal

Add an optional Chinese poster-copy mode to the slim online image without changing the default English behavior, and improve the offline-cache Docker Compose documentation so users clearly understand how the slim and offline-enhanced modes are meant to be used.

## Product Decision

- Default behavior stays aligned with the original project: poster city/country copy is English unless the user explicitly overrides it.
- Add a user-facing poster-copy language selector with two choices:
  - `默认英文`
  - `中文`
- Chinese mode is opt-in only.
- Existing manual title/subtitle override fields keep highest priority.
- The new feature must not change current behavior for users who do nothing.

## User Experience

### Default English Mode

If the user leaves the new language selector at `默认英文`:

- the current automatic English city/country extraction remains unchanged
- existing posters should continue to render the same way as before
- current users are not forced into Chinese output

### Chinese Mode

If the user selects `中文`:

- if they manually typed poster title/subtitle, those values still win
- otherwise the app should try to extract Chinese city and country names
- when Chinese output is chosen, the app should automatically load the Chinese font path
- if Chinese geographic naming cannot be resolved, the app should gracefully fall back instead of failing the request

## Poster Copy Priority

The final title/subtitle selection order should be:

1. User-entered `display_city` / `display_country`
2. Auto-resolved Chinese city/country names when language mode is `中文`
3. Existing English auto-resolved city/country names

This preserves explicit user intent and keeps fallback behavior predictable.

## UI Changes

Add a new selector near the existing poster copy fields:

- label: `海报文案语言`
- values:
  - `英文（默认）`
  - `中文`

Add short helper text explaining:

- 默认仍为英文文案
- 选择中文后，只会替换自动生成的城市/国家名称
- 手动输入的标题/副标题优先级更高

## Backend Changes

### Form Contract

Add a new form field, for example:

- `copy_language`

Accepted values:

- `en`
- `zh`

Default:

- `en`

### Geocoding Strategy

Keep the current English geocoding flow for default mode.

For Chinese mode:

- still resolve the location normally
- additionally attempt to obtain a Chinese-address version for city/country display
- use that Chinese result only for poster copy, not to change the existing coordinate behavior

This avoids changing the geographic lookup semantics while still supporting Chinese poster copy.

### Font Loading

Chinese mode should trigger Chinese font loading when the final rendered copy includes Chinese characters.

If the user selects Chinese mode but the final text still ends up non-Chinese due to fallback behavior, the existing font logic should remain safe.

## Error Handling

- If Chinese copy extraction fails, do not fail the poster request.
- Fall back to the existing English copy path.
- Keep the response predictable and avoid surprising blank labels.

## Offline Compose Documentation Improvements

Clarify the two intended usage modes:

### Slim Online Mode

- uses the main app image only
- first request downloads required map data online
- later requests benefit from cache reuse
- now also supports the optional Chinese poster-copy mode

### Offline-Enhanced Mode

- uses `docker-compose.offline-cn.yml` together with the base compose file
- seeds the shared cache volume on first startup
- still supports online fallback for cache misses
- also supports the optional Chinese poster-copy mode

The documentation should explicitly state that the current offline workflow is:

- slim application image
- separate offline seed image / seed flow
- named volume for persisted cache reuse

## Testing Scope

Implementation should verify:

1. The new language selector defaults to English
2. Choosing English preserves existing behavior
3. Choosing Chinese uses Chinese copy when available
4. Manual display overrides still beat automatic copy in both modes
5. Chinese mode falls back safely when Chinese copy cannot be resolved
6. Documentation mentions both slim and offline-enhanced modes clearly

## Out Of Scope

- Changing the default poster language to Chinese
- Replacing the existing manual title/subtitle override mechanism
- Full offline Chinese geocoding
- Publishing a fully built offline seed image in this spec by itself

## Recommended Next Step

Write an implementation plan covering:

- UI selector addition
- backend language selection and fallback handling
- minimal tests for language selection behavior
- compose and README documentation updates
