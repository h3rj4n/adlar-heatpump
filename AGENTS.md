# AGENTS.md

## Project overview
This repository contains a Home Assistant custom integration.

Primary goals for any change:
- Preserve Home Assistant conventions and async-first design.
- Keep the integration configurable via the UI when possible.
- Avoid breaking entity unique IDs, config entries, and user-visible entity names.
- Prefer small, reviewable changes over broad refactors.
- Update tests and docs with every behavior change.

## Repository assumptions
Typical structure for this integration:

- `custom_components/adlar_heatpump/__init__.py` — integration setup and teardown
- `custom_components/adlar_heatpump/manifest.json` — metadata, requirements, integration type
- `custom_components/adlar_heatpump/config_flow.py` — UI-based setup
- `custom_components/adlar_heatpump/coordinator.py` — DataUpdateCoordinator logic, if used
- `custom_components/adlar_heatpump/entity.py` — shared entity base classes
- `custom_components/adlar_heatpump/sensor.py` / `binary_sensor.py` / `switch.py` etc. — platforms
- `custom_components/adlar_heatpump/services.yaml` — service descriptions, if any
- `custom_components/adlar_heatpump/translations/` — localization files
- `tests/components/adlar_heatpump/` — pytest coverage for the integration

If the repo differs, follow the existing layout rather than forcing a new one.

## Working rules
- Use **async** APIs wherever Home Assistant expects them.
- Do not block the event loop with network I/O, sleeps, or heavy CPU work.
- Prefer `aiohttp`/async client libraries over sync libraries when possible.
- Reuse existing coordinator/client patterns already present in the repo.
- Keep imports scoped and minimal; do not introduce new dependencies unless necessary.
- Do not rename the integration domain.
- Do not change `unique_id` generation logic unless explicitly required and migration-safe.
- Never hardcode secrets, tokens, or hostnames.

## Home Assistant conventions
- Follow Home Assistant developer docs and existing core integration patterns.
- New user setup should go through a config flow when feasible.
- Validate setup as early as possible so failures happen before partial initialization.
- Raise user-relevant errors through the proper Home Assistant flow/repair mechanisms, not silent failures.
- Entities should expose only meaningful attributes; avoid noisy or redundant extra state attributes.
- Use device info consistently so entities are grouped correctly in the device registry.
- Prefer coordinators for polled APIs and dispatcher/callback patterns for push updates.
- Keep logging useful but not noisy; never log credentials or raw secrets.

## Manifest expectations
When editing `manifest.json`:
- Keep required fields valid and minimal.
- Ensure dependency versions are intentional.
- Update documentation links if present.
- Confirm `integration_type` is correct.
- If quality scale metadata files are present, keep them in sync with the implemented behavior.

The Home Assistant manifest and quality scale docs are the source of truth for required metadata and expectations. New integrations in Home Assistant core are expected to meet at least Bronze quality scale requirements, and the quality scale also includes documentation and testing expectations. 

## Config flow guidance
When editing `config_flow.py`:
- Preserve stable step IDs and flow behavior unless the change requires a migration.
- Validate user input with clear error mapping.
- Prevent duplicate entries by checking unique identifiers where applicable.
- Support reauth/reconfigure flows if the integration already has those patterns.
- Add or update config flow tests for every branch you change.

## Entities
When adding or modifying entities:
- Use `has_entity_name = True` unless the repo intentionally does otherwise.
- Ensure `unique_id` is stable across restarts.
- Set `device_class`, `state_class`, `unit_of_measurement`, and `entity_category` only when appropriate.
- Do not expose rapidly changing diagnostic data as primary entity state.
- Put diagnostics/configuration values in diagnostic entities or diagnostics output where appropriate.
- Maintain backward compatibility for entity IDs whenever possible.

## Coordinator and update logic
If the integration uses `DataUpdateCoordinator`:
- Keep fetch logic inside the coordinator or API client, not in entity properties.
- Entities must read cached coordinator data rather than doing their own I/O.
- Use targeted refreshes when possible instead of broad reloads.
- Handle partial API failures gracefully.
- Surface availability based on real upstream state.

## Error handling
- Fail clearly, not silently.
- Convert API/client exceptions into Home Assistant exceptions or flow errors where appropriate.
- Use retries and backoff only where they already fit the project design.
- Mark entities unavailable instead of returning misleading stale values when data is invalid.
- Log concise actionable messages with enough context for debugging.

## Tests
Run the smallest relevant test scope first, then broader validation if needed.

Common commands:
- `pytest tests/components/<domain> -q`
- `pytest tests/components/<domain>/test_config_flow.py -q`
- `ruff check custom_components/<domain> tests/components/<domain>`
- `python -m compileall custom_components/<domain>`

If this repository includes Home Assistant’s full test tooling, also run any documented project-specific commands.

Testing expectations:
- Add or update tests for each functional change.
- Cover happy path, failure path, and setup validation.
- For config flow changes, include flow coverage.
- For entity changes, verify state, availability, and unique ID behavior.
- For coordinator changes, test refresh failures and recovery.

Home Assistant’s quality scale includes config-flow coverage, documentation quality, and high overall test coverage expectations, so code changes should move the repo toward those standards rather than away from them.

## Documentation updates
When behavior changes, review whether these also need updates:
- `README.md`
- integration docs
- service/action docs
- automation examples
- troubleshooting notes
- supported devices/features list
- limitations / known caveats

Home Assistant’s integration documentation guidance explicitly expects installation instructions, high-level descriptions, and—at higher quality tiers—examples, supported devices/functions, troubleshooting, update behavior, and known limitations.

## Translations
If you change:
- config flow strings
- options flow strings
- abort/error reasons
- service descriptions
- repair issue text

Then update the translation files consistently and preserve existing translation key structure.

## Dependency changes
Before adding a dependency:
- Prefer existing stdlib or current project utilities.
- Prefer async-compatible libraries.
- Keep the dependency surface small.
- Explain why the dependency is needed in the PR or commit notes.
- Update tests to cover the new integration boundary.

## Safe change strategy
1. Read the existing integration structure first.
2. Change the smallest number of files that can solve the problem.
3. Preserve public behavior unless the task explicitly changes it.
4. Run lint/tests for the touched area.
5. Update docs and translations if user-visible behavior changed.

## Forbidden changes
Do not:
- rewrite the integration into a different architecture without need
- replace async code with sync code
- break config entry migration paths
- change entity naming/IDs casually
- add speculative features not requested
- remove tests without replacement
- commit credentials, tokens, or local URLs

## Preferred output for coding agents
When making changes:
- summarize what changed
- note any migrations or breaking risks
- list tests run
- mention any follow-up work still needed
