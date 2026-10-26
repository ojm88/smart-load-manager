# Smart Load Manager OJM – enkel brukerveiledning

## Hva hjelper integrasjonen med?

Den passer på at huset holder seg innenfor **Forbruksgrense** i løpet av timen. Den leser strømmen fra HAN-måleren og hvor mye energi som allerede er brukt. Deretter justerer den hvor raskt Easee-laderen lader, slik at det blir plass til resten av huset.

Høye forbrukstopper kan gi dyrere effektledd på strømregningen. Ved å unngå slike topper kan noen husholdninger spare flere tusen kroner i året. Hvor mye det betyr, kommer an på strømavtalen og forbruket hjemme. Besparelse er ikke garantert.

### Bakgrunnen

I Norge kan nettleien bli høyere når boligen bruker mye strøm samtidig. Smart Load Manager prøver derfor å flytte ladingen av elbilen til timer der huset har bedre plass innenfor grensen du har valgt. Målet er å unngå unødvendige forbrukstopper – ikke å love en bestemt besparelse. Nettleie og trinn er forskjellige fra nettselskap til nettselskap. [Glitre Nett forklarer sine priser og trinn her](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde).

Vi har valgt styrbare laster som kan vente litt. Varmtvann og varmekabler kan være aktuelle å støtte senere fordi de kan lagre varme. Integrasjonen styrer foreløpig bare Easee-lading. Den prøver ikke å styre lys, matlaging, tørketrommel eller varmepumpe – slike ting må kunne brukes når familien trenger dem.

Integrasjonen prøver ikke å finne den billigste spotpristimen. Tidsstyring kan likevel legge ladingen til natten, når nettleien hos mange nettselskaper er lavere. Norgespris og strømpris er egne deler av regningen; hovedmålet her er å holde forbruket under ønsket effekttrinn.

Smart Load Manager bygger på åpen kildekode og fellesskapets arbeid. Home Assistants Easee-integrasjon gir tilgang til laderen, og EnergyTariff av Erling Paulsen leverer timeforbruket som brukes i beregningen. Takk til dem og alle som deler løsninger med Home Assistant-fellesskapet. Varmestyring med [Versatile Thermostat (VTherm)](https://github.com/jmcollin78/versatile_thermostat) er mulig inspirasjon for framtidig arbeid; den er ikke en del av integrasjonen nå.

## Før du begynner

Home Assistant-integrasjonene for **Easee** og **EnergyTariff** må være installert og satt opp først. Du trenger en HAN-sensor for øyeblikkelig effekt i W eller kW, og EnergyTariff-sensoren som viser forbruk hittil denne timen. Bruk samme HAN-sensor som EnergyTariff.

I oppsettet velger du laderen, HAN-måleren, EnergyTariff-sensoren og en sikkerhetsmargin. Etterpå velger du **Forbruksgrense** på Smart Load Manager-enheten. Dette er timegrensen som Smart Load Manager styrer etter.

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

Sensoren **Ladeforklaring** bruker vanlige ord for å fortelle hvorfor bilen lader, venter eller får mindre strøm.

## Kort på dashboardet

For en eksisterende dashboard-seksjon: velg **Legg til kort → Manuelt**, åpne YAML-editoren og lim inn hele `examples/lovelace/charging_card.yaml`. Dette er ett kort.

Grafen bruker disse verdiene:

- `sensor.slm_recommended_current` – Anbefalt strøm
- `sensor.energy_used_this_hour` – Brukt
- `sensor.slm_charger_current` – Målt ladestrøm
- `sensor.energy_estimate_this_hour` – Timeestimat
- `sensor.average_peak_hour_energy` – Snitt 3-timer

Brukt, Timeestimat og Snitt 3-timer hentes direkte fra EnergyTariff. Smart Load Manager lager ikke ekstra kopier for grafen.

## To ladere

Legg til den andre Easee-laderen via **Innstillinger → Enheter og tjenester → Smart Load Manager → Konfigurer → Legg til lader**. Laderens navn hentes fra Easee. Målekilder, sikkerhetsmargin og Forbruksgrense er felles; hver lader får egne styringer og sensorer. Slå på automatisk laststyring for hver lader som skal delta.

- **Lad begge:** Ledig effekt deles likt. Når det bare er plass til én, får laderen valgt under **Førsteprioritet** lade. Hvis kapasiteten ikke rekker til minimumslading, venter ladingen.
- **Én om gangen:** Prioritert lader får lade til bilen avslutter. Den andre kan også lade hvis prioritert lader er frakoblet, manuelt pauset eller utenfor sin ladetid.
- **Råd om fasevalg:** Foreslår enfase når dette kan gi plass til begge. Fasevalg endrer du selv for hver lader. Ikke alle biler støtter alle ladeformer.

«Bilen har avsluttet ladingen» er laderens tilbakemelding; integrasjonen kjenner ikke batteriprosenten. En manuelt pauset lader skal forbli pauset. Manuell strøm når automatisk styring er av inngår som øvrig husforbruk, ikke i den automatiske fordelingen.

Bytt det gamle kortet med **examples/lovelace/two_chargers_card.yaml**. For YAML med riktige sensor-ID-er: åpne **Utviklerverktøy → Handlinger**, kjør `smart_load_manager.get_dashboard`, kopier innholdet i `yaml`-svaret og lim inn som ett manuelt kort i en eksisterende seksjon. Alternativt erstattes `CHARGER_SUFFIX` i eksempelfilen med `card_suffix` fra den nye laderens Råd om fasevalg-sensor. Felles Markdown forklarer lademåte, prioritet og hvorfor hver lader lader eller venter. Ingen full view-mal brukes.

## Trygg test

1. Ta en sikkerhetskopi og noter hvordan du slår på den gamle automasjonen igjen.
2. Slå av den gamle automasjonen, men ikke slett eller endre den.
3. Installer integrasjonen og start Home Assistant på nytt. La automatisk laststyring være av.
4. Kontroller at måler, forbruk hittil, fase/spenning, anbefalt strøm og Easee-grenser ser riktige ut.
5. Når du er til stede og klar til å følge laderen, slå på automatisk laststyring. Bekreft at anbefalingen og Easee-grensen følger hverandre.
6. Ved feil: slå av automatisk styring og slå på den gamle automasjonen igjen. Ikke la begge styre laderen samtidig.

Automatiske tester dekker beregning og tjenestekall. De kan ikke bekrefte oppførselen i ditt elektriske anlegg; det må kontrolleres i Home Assistant og med Easee-laderen.

Ved test med to ladere: kontroller begge fordelingsvalg, bytte av førsteprioritet, pause, frakobling og at den andre overtar når bilen avslutter. Nye funksjoner er automatisk testet; fysisk tolader-test må gjennomføres.
