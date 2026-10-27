# Smart Load Manager OJM – brukerveiledning

SLM tilpasser ladingen til boligens valgte timebudsjett. Målet er å redusere unødvendige effekttopper og dermed kunne holde nettleien på et lavere kapasitetstrinn. Det er ingen garanti for besparelse og ingen spotprisoptimalisering.

## Før du begynner

- Home Assistant 2026.2 eller nyere.
- Easee-integrasjonen og EnergyTariff må være satt opp.
- Bruk HAN-sensoren som EnergyTariff benytter (W eller kW).
- Aktiver **Spenning/Voltage på hver Easee-lader**, også lader nummer to: Innstillinger → Enheter og tjenester → Easee → laderen → Entiteter. Vis deaktiverte entiteter og vent på en målt verdi.

## Installasjon og oppsett

Last ned ønsket GitHub-utgivelse. Kopier `custom_components/smart_load_manager` til `config/custom_components/`, og start Home Assistant på nytt.

Fra HA 2026.11 kan du også legge til `https://github.com/ojm88/smart-load-manager` som egendefinert integrasjonsrepo i **Innstillinger → Marketplace**. Egendefinerte repoer krever GitHub-tilkobling.

1. Legg til **Smart Load Manager OJM** under Enheter og tjenester.
2. Velg boligens HAN-effekt, EnergyTariff **brukt denne timen**, og sikkerhetsmargin.
3. Velg elbillading og første Easee-lader. Velg deretter å fullføre med én eller legge til en til. Listen for lader to viser bare enheter du ikke allerede har valgt.
4. Velg **Forbruksgrense** på **SLM – Boligen** (4,5–20 kWh per time, trinn på 0,5).
5. Slå av eventuell tidligere automasjon som regulerer de samme laderne. Slå deretter på automatisk laststyring for laderne du vil styre.

Ingen egne hjelpere eller YAML-automasjoner trengs. Varmtvann og gulvvarme vises bare som planlagte funksjoner.

## Boligen og lading

**Boligen** har felles forbruksgrense, samlet status og målegrunnlag. Med to ladere ligger også **Lademåte** her. **Lading** samler begge laderne med hver sine innstillinger og målinger.

| Betjening | Funksjon |
| --- | --- |
| Automatisk laststyring | Lar SLM regulere laderen. Starter avslått etter omstart. |
| Ladepause | Sender 0 A. Ved gjenopptak beregnes ny strøm automatisk, eller tidligere manuell grense gjenopprettes når målinger og grenser tillater det. |
| Manuell ladestrøm | Tilgjengelig når automatikk og ladepause er av. Easees rapporterte øvre grense gjelder. |
| Fasevalg | Endrer Easees faseinnstilling. SLM bytter ikke automatisk mellom én og tre faser. |
| Tidsstyring og starttid | Eget daglig 12-timers ladevindu per lader. Åpent vindu gir bare tillatelse til lading. |
| Førsteprioritet | Vises med to ladere. Bryterne er koblet sammen, slik at nøyaktig én har førsteprioritet. Dette endrer ikke Easees tekniske master/slave-oppsett. |

**Lad begge** fordeler ledig effekt likt innenfor hver laders strømgrenser. Når bare én får plass, prioriteres den valgte laderen. **Én om gangen** gir den prioriterte, tilgjengelige laderen tur først. Frakobling, pause, avsluttet lading og stengt tidsvindu kan gi den andre laderen tur.

Minste strøm er 11 A ved målt 230 V trefaselading, ellers 6 A. SLM henter øvre strømgrense fra Easee; den skal ikke tastes inn i SLM. Bilen identifiseres ikke, og «Completed» bekrefter ikke batteriprosent.

## Målinger og navn

Seks hovedsensorer per lader: **Ladestatus**, **Effekt til bilen**, **Strøm til bilen**, **Anbefalt ladestrøm**, **Faser i bruk** og **Volt**. Funksjonen kommer først og ladernavnet sist, også for første lader. Volt viser målt eller utledet spenning mellom fasene; fase–nøytral og øvrige elektriske detaljer finnes på Ladestatus.

**Anbefalt ladestrøm** har minimum og Easees maksimum som attributter. **Status for laststyring** på boligen forklarer hvorfor hver lader lader eller venter, med eventuelle faseråd. **Målegrunnlag** viser målekilder, HAN-alder og målingenes gyldighet. Ladeprioritet er en diagnostikksensor ved to ladere.

## Dashboard

Kjør `smart_load_manager.get_dashboard` under **Settings → Tools → Actions**. Kopier `yaml` til et **Manuelt kort i en eksisterende seksjon**. Generatoren bruker de faktiske entitets-ID-ene, også når du har gitt dem egne navn. Grafen leser EnergyTariff direkte.

De statiske [ett-lader](../examples/lovelace/charging_card.yaml)- og [to-lader](../examples/lovelace/two_chargers_card.yaml)-kortene er maler. Generer helst kortet for din installasjon.

## Konfigurasjon

**Konfigurer → Boligens målekilder og sikkerhetsmargin** validerer alt før lagring og påvirker ikke ladeinnstillingene. Nye kilder leses ved neste ordinære oppdatering.

**Konfigurer → Ladere → Legg til lader** viser bare ledige Easee-enheter og beholder den eksisterende laderen. **Fjern lader** er et eget valg når to ladere er konfigurert. Integrasjonen lastes på nytt, og automatisk styring må aktiveres igjen. En lader som fjernes, får en 0 A-kommando før oppsettet endres; feil ved denne kommandoen avbryter endringen. Dette er ikke en målt bekreftelse på at fysisk lading har stoppet. Innstillinger beholdes ved senere gjeninnlegging.

## Hvis lading venter

Les først boligens status og Målegrunnlag. Kontroller HAN, EnergyTariff, aktiv Easee-spenningssensor, rapportert strømgrense, pause og tidsvindu. HAN må være gyldig og høyst 60 sekunder gammel. En uendret, tilgjengelig Easee-effektverdi er gyldig selv med gammelt tidsstempel. Fordeling venter på nye målinger som bekrefter en reduksjon før mer strøm gis til den andre laderen.

SLM erstatter ikke vern eller installasjonens elektriske begrensninger. Automatikk av betyr at SLM slutter å regulere; Easee beholder siste dynamiske grense. Bruk Ladepause for en uttrykkelig 0 A-kommando.

## Valg av ladere

Hele oppsettet skjer i Home Assistants vanlige dialog, også i Companion-appen. Velg **Elbillading – Easee**, velg første lader i listen, og fullfør med én eller legg til en til. Den andre listen utelater laderen du allerede har valgt. Listen viser ladernavn uten logoer.

Ved senere tillegging brukes **Legg til lader** under Konfigurer → Ladere. Bare ledige Easee-ladere vises, og eksisterende lader og innstillinger beholdes. Avbryter du førstegangsoppsettet før fullføring, opprettes ingen delvis installasjon.

### Når må dashboardkortet genereres på nytt?

Kjør `smart_load_manager.get_dashboard` og erstatt YAML-en i det eksisterende manuelle kortet når du legger til, fjerner eller bytter lader, endrer HAN-kilde eller entitets-ID-er som kortet bruker, endrer ladernavn som står i kortoverskriftene, eller tar i bruk en funksjon med endret kortoppsett. Kortets YAML oppdateres ikke automatisk. Vanlige endringer i forbruksgrense, sikkerhetsmargin, prioritet, lademåte, tidsplan, fasevalg og pause krever ikke nytt kort; verdiene oppdateres i visningen. Ta vare på egne manuelle korttilpasninger før du erstatter YAML-en.
