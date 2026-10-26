# 0.1.1-beta.4

## Included

- Fix two-charger outages caused by the 120-second power-report cutoff. Easee reports power on changes; unchanged available readings remain usable. HAN freshness and reduction acknowledgement remain required.
- Show actionable errors for required Easee Voltage sensor activation, for every charger.
- Allow editing shared HAN/EnergyTariff sources and safety margin after setup, also with two chargers.
- Add SLM – Boligen with household Forbruksgrense, one plain-language Load control status sensor and shared measurement diagnostics.
- Five main measurement sensors per new charger; retain existing sensors as compatibility diagnostics.
- Updated one-/two-charger Manual cards render household explanations centrally. Graphs still use EnergyTariff directly.
- Installation and usage documentation updated with Marketplace terminology.

## Not included yet

The new household-first initial wizard, complementary master toggles, conditional pair-control lifecycle and charger-ID naming migration are still pending. Beta.4 retains the existing one-at-a-time setup flow and First priority dropdown. Hot-water and floor-heating control are not implemented. Existing entity IDs are retained.

## After upgrading

Restart Home Assistant. Enable the Easee Voltage sensor on each charger if needed. Generate the updated one-/two-charger card using `smart_load_manager.get_dashboard` and replace the old Manual card in your existing dashboard section. Old sensor references continue to work.

## Validation

56 pure unit tests and 31 mocked Home Assistant runtime tests passed locally. No physical beta.4 two-charger test is claimed. Test the two-charger fix, settings editor and new cards in your installation; do not run the old automation and SLM automatic control together.
