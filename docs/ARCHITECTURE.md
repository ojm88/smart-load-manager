# Smart Load Manager: household control and explanations

## One household, independent loads

Forbruksgrense is a household limit. The **SLM – Boligen** Home Assistant device
holds shared configuration and information, not one charger's priority role.
One installation config entry owns household sources, site options and saved load records. Native household and charging subentries group devices. LoadEntry adapters retain the original load IDs and per-load settings; a charger priority never owns the budget. A standalone heating-only installation and thermal control remain future work.

## Responsibilities

| Layer | Responsibility |
| --- | --- |
| Easee / HAN / EnergyTariff sources | Measurements and charger feedback. |
| Charger coordinator | Read/validate sources and derive electrical and schedule information. |
| Shared site allocator | Distribute the household budget and serialize commands/acknowledgements. |
| `household_status.py` | Describe already calculated decisions in plain language; no allocation or commands. |
| `sensor.slm_status` | One household status and structured `controlled_loads` attributes for the UI. |
| Markdown | Render the shared explanation and per-load rows; do not reproduce control rules. |

The distinction matters: commanded/recommended current and measured charging are
separate facts. A waiting or missing peer must be explicitly represented.
Completing charging is not proof of battery state. Device hardware master/slave
roles are separate from SLM's software priority.

## Information contract and later extensions

`summary` explains the home as a whole; `distribution_explanation` explains the
charging mode. `controlled_loads` contains one row per configured load with its
stable ID, real name, type, measured state, recommended current, eligibility and
plain-language explanation. Shared phase advice appears once, not on every
charger. Detailed source failures remain in per-load `control_detail` attributes
and the separate shared Measurement status diagnostic.

Before adding hot-water/floor-heating support, extend the load adapter and the
central description builder for that load type. Add appropriate tests for both
control and explanation; keep the Markdown a renderer of this contract. Current
rows and explanations support EV chargers only. Do not add parallel information
sensors on each new load just to feed a dashboard.

Site sampling publishes one complete multi-charger snapshot before notifying
entities. The household status reads that snapshot so a peer's previous cycle
is not mixed with a new allocation. Single-charger mode reads its coordinator
payload directly. The presenter does not infer any additional control decision.

## Diagnostics and compatibility

The six main charger measurements are status, power, measured current,
recommended current, active phases and voltage. Current limits and electrical details
are attached to their owning measurement. Household explanations and advice
belong only on the household sensor in new installations. Previously registered
sensors are retained as compatibility diagnostics with their identities intact.

Both YAML examples and packaged templates use the same household sensor. The
Get dashboard action resolves registry IDs and source entity names; no data is
copied from EnergyTariff solely for graphs. Generated IDs include saved charger-name identities from the first load. Registry migration preserves unique IDs and user customizations, records old/new mappings, and leaves external YAML edits to the owner.


## Beta.16 category controls and diagnostics

Charging-category commands batch existing EV controller flags under the site lock. Switching automatic charging off stages the validated allowed manual minimum. Manual requests use fresh site sampling, schedule/input guards and paired measured reduction before increases; they do not use the automatic hourly allocation target. Startup still never sends a positive manual default. The dashboard groups normalized rows by configured load category and keeps household measurements separate. Thermal control adapters remain future work.

DebugTrace keeps 4096 allowlisted anonymous events in memory, covering sampling, regulation decisions and command service outcomes. Native HA diagnostics exports these plus current load state and versions. No raw configuration/errors/registry fields are exported. New functionality must extend the relevant event and snapshot contracts and privacy/failure-sequence tests. Diagnostic success records describe HA service completion, not physical acknowledgement.
