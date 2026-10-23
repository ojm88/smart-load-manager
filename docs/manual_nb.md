# Smart Load Manager OJM – enkel brukerveiledning

## Hva hjelper integrasjonen med?

Den passer på at huset holder seg innenfor **Forbruksgrense** i løpet av timen. Den leser strømmen fra HAN-måleren og hvor mye energi som allerede er brukt. Deretter justerer den hvor raskt Easee-laderen lader, slik at det blir plass til resten av huset.

Høye forbrukstopper kan gi dyrere effektledd på strømregningen. Ved å unngå slike topper kan noen husholdninger spare flere tusen kroner i året. Hvor mye det betyr, kommer an på strømavtalen og forbruket hjemme. Besparelse er ikke garantert.

## Før du begynner

Home Assistant-integrasjonene for **Easee** og **EnergyTariff** må være installert og satt opp først. Du trenger en HAN-sensor for øyeblikkelig effekt i W eller kW, og EnergyTariff-sensoren som viser forbruk hittil denne timen. Bruk samme HAN-sensor som EnergyTariff.

I oppsettet velger du laderen, HAN-måleren, EnergyTariff-sensoren og en sikkerhetsmargin. Etterpå velger du **Forbruksgrense** på Smart Load Manager-enheten. Dette er timegrensen som Smart Load Manager styrer etter. EnergyTariff leverer målt forbruk og estimat; EnergyTariff sin egen grense kopieres ikke hit.

Du trenger ikke å lage egne hjelpere eller automasjoner i YAML.

## Slik styrer du ladingen

- **Automatisk laststyring:** Slå på når du vil at integrasjonen skal regulere Easee etter timegrensen. Den er avslått etter installasjon og omstart.
- **Forbruksgrense:** Velg ønsket energimengde for hele huset denne timen. Valgene går fra 4,5 til 20 kWh.
- **Fasevalg:** Velg én fase, tre faser eller la Easee velge automatisk.
- **Manuell ladestrøm:** Brukes når automatisk laststyring er av. Skyveren er da en enkel måte å sette Easee-grensen på. 0 A betyr pause.
- **Ladepause:** Slår ladingen av og på via Easee. Pause sender 0 A. Når du slår av pausen, regner automatisk styring ut en ny grense. I manuell modus forsøker integrasjonen å sette tilbake forrige grense, men bare hvis målingene og Easee-grensene fortsatt tillater det.
- **Tidsstyring:** Valgfri plan som åpner for lading i 12 timer fra valgt starttid.

Easee beholder sist sendte dynamiske grense når automatisk laststyring slås av. Den gamle automasjonen må derfor være avslått mens du tester automatisk styring, så de to ikke sender ulike grenser samtidig.

## Hva betyr minste strøm?

Minste ladestrøm følger den avtalte faste regelen: **11 A** ved målt 230 V trefaselading, ellers **6 A**. Integrasjonen lærer ikke bilens oppførsel.

Hvis HAN-målingen, EnergyTariff-dataene eller Easee-grensene mangler eller ikke er gyldige, holder automatisk styring laderen på 0 A. Kortet viser hvorfor den venter eller begrenser ladingen.

Sensorn **Ladeforklaring** bruker vanlige ord for å fortelle hvorfor bilen lader, venter eller får mindre strøm.

## Kort på dashboardet

For en eksisterende dashboard-seksjon: velg **Legg til kort → Manuelt**, åpne YAML-editoren og lim inn hele `examples/lovelace/charging_card.yaml`. Dette er ett kort. Ikke lim inn `charging_view.yaml` i korteditoren.

Grafen bruker disse verdiene:

- `sensor.slm_recommended_current` – Anbefalt strøm
- `sensor.energy_used_this_hour` – Brukt
- `sensor.slm_charger_current` – Målt ladestrøm
- `sensor.energy_estimate_this_hour` – Timeestimat
- `sensor.average_peak_hour_energy` – Snitt 3-timer

De tre siste måler verdier direkte fra EnergyTariff. Smart Load Manager lager ikke ekstra kopier for grafen.

## Trygg test

1. Ta en sikkerhetskopi og noter hvordan du slår på den gamle automasjonen igjen.
2. Slå av den gamle automasjonen, men ikke slett eller endre den.
3. Installer integrasjonen og start Home Assistant på nytt. La automatisk laststyring være av.
4. Kontroller at måler, forbruk hittil, fase/spenning, anbefalt strøm og Easee-grenser ser riktige ut.
5. Når du er til stede og klar til å følge laderen, slå på automatisk laststyring. Bekreft at anbefalingen og Easee-grensen følger hverandre.
6. Ved feil: slå av automatisk styring og slå på den gamle automasjonen igjen. Ikke la begge styre laderen samtidig.

Automatiske tester dekker beregning og tjenestekall. De kan ikke bekrefte oppførselen i ditt elektriske anlegg; det må kontrolleres i Home Assistant og med Easee-laderen.
