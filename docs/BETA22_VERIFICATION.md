# Beta 22 preparation — 2026-11-01

Not published; manifest remains beta 21. Owner confirms beta 21 starts charging on the outside charger with one connected car and two configured chargers. This does not yet establish simultaneous paired capacity transfer.

## Scope and source contracts

- Always-Norwegian household presentation payload feeds the existing Norwegian Markdown. HA server language continues to govern ordinary translated entity metadata.
- Remove the combined charging-automation entities card from two-charger packaged/example YAML. Retire the obsolete combined switch by unique ID and its empty SLM-owned category device, retaining the Charging grouping, per-charger persisted choices and unrelated registry entries. Add read-only household charging overview and total measured charger power; use the same samples, include manual draw and expose no total if a peer is missing. Diagnostic summary uses anonymous aliases.
- Native additive SelectSelector still excludes configured devices and caps additions. Installed HA selector.py confirms SelectOptionDict has only value/label, and DeviceFilterSelectorConfig has no individual-ID exclusion. Add a small Easee brand image to the native dialog description; dropdown options remain text. No external navigation/custom panel.
- Optional household energy_estimate_entity selects total estimated current-clock-hour kWh. Legacy fallback sensor.energy_estimate_this_hour is retained if omitted. Validate finite nonnegative kWh at selection; invalid/unavailable runtime values yield no estimate and do not affect charging readiness. Source-event subscription, normal/partial sampling and graph references use the selected source.
- Hourly consumed energy remains a separate required input. Tibber accumulated consumption current hour can provide it; estimated consumption cannot replace it. EnergyTariff remains recommended for its additional sensors. Official Tibber documentation lists the hourly estimate: https://www.home-assistant.io/integrations/tibber/.

## Validation

93 pure tests, 161 HA runtime tests on each supported environment (2026.10.4/Python 3.14.8 and 2026.2.3/Python 3.13.16), and one Node test pass. Compilation, JSON parsing, YAML loading and whitespace checks pass. Runtime tests include selected-source live events and loss, setup unit/numeric validation, legacy estimate fallback, actual registered graph references and Norwegian rendered Markdown on an English server. Existing charge cadence, paired handover, completion/wake and persistence suites pass with synthetic telemetry and mocked outgoing commands.

## Remaining acceptance

No production HA writes, physical charging commands or phone rendering during this preparation. Dialog logo placement/rendering must be checked in Companion; it is not restored inside individual dropdown options. Regenerate YAML after installing a future release to get the removed card and changed source references. A two-car hardware test remains part of beta 21 acceptance.

Real registry tests verify renamed/disabled old-toggle cleanup, idempotence, preserved individual settings/entity identity and retention of unrelated device entities. Summary tests cover mixed automatic/manual draw and missing/nonfinite peer power. Individual-control test verifies toggling one charger leaves its peer enabled. These replace tests of the deliberately removed global toggle.


## Observed consumption reservation — 2026-11-02

Added a separate consumption forecast estimator; it never changes configured maxima. 180-second stable positive charging draw permits measured power +100 W rather than an indefinite full-offer reservation. New commands/demand changes, zero/waiting and invalid inputs reset observation. Settled manual reservation uses the same estimate; pending manual requests still reserve their whole target. Existing automatic allocation does not gain a learned demand cap. Four pure sequence tests cover hidden caps, startup, restart/rising demand, invalid/zero states and unequal phase/manual operation. A site runtime regression checks the actual forecast argument and retains serialized apply. No live app changes, physical acceptance or production HA writes.

Reservation refinement validation: 97 pure tests and 162 runtime tests pass on EACH HA 2026.2.3/Python 3.13.16 and HA 2026.10.4/Python 3.14.8. Compilation and whitespace checks pass. Physical hidden-app-limit change and demand rebound remain unverified.

## Same-session pause retention — 2026-11-02

Supersedes the waiting/zero reset above. Settled observations survive connected waiting/zero-draw pauses and zero/resume command changes. No reduced reservation is used while waiting: a complete positive offer stays reserved until positive charging matches the learned demand within 100 W. Reuse requires unchanged factor, phase mode and automatic/manual context, and an offer no higher than the observed offer. Completed/disconnected (including charged alias), faults/unknown/offline, invalid inputs and context changes discard memory; rising/falling demand or higher offers start conservative observation again. Unsettled draw cannot accrue its 180 seconds during a pause. Memory remains per charger and resets on reload/site input failure. Allocation maxima, command cadence and active transfer guards are unchanged.

Validation: 104 pure tests and 164 runtime tests pass on EACH HA 2026.2.3/Python 3.13.16 and HA 2026.10.4/Python 3.14.8. Compilation and whitespace checks pass. Seven added pure scenarios cover source ordering, repeated pauses, unlearned pauses, completion/unplug/relearning, rebound/higher offers, invalid/phase/mode changes and independent manual three-phase peers. Two added full site-refresh scenarios exercise one/two chargers, manual stop/resume, actual automatic forecast-risk zero commands, measured reduction confirmation and budget recovery, completion and unplug. Samplers and outgoing commands are synthetic; no live HA or charger operations. Against preceding beta-22 code, the new pure suite fails six subcases and the site suite fails four subcases; restored implementation passes both full suites. The unchanged Node check retains its prior validation record.

Physical acceptance still required: charge with a stable app-side limit, let household demand force a temporary SLM stop, then confirm that resumed matching draw avoids a new three-minute observation. End the session or unplug and verify that a new session starts conservative learning again. This does not resolve the separate shared-circuit finding. No beta publication or production installation performed.
