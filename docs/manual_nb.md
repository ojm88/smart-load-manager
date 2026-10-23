# Brukermanual — Smart Load Manager OJM beta.14

## Hva beta 14 retter

Beta 14 retter både en manglende verdi som hindret sensorplattformen i å starte, og registreringen av korte ID-er. `sensor.slm_*` brukes nå som faktisk entity-ID i Home Assistant. Ved oppgradering flyttes eksisterende sensor-ID-er over til de nye navnene. Home Assistant-entitetenes unike ID-er beholdes. **Forbruksgrense** beholder den avtalte ID-en `select.smart_load_manager_ojm_easee_forbruksgrense`. Hvis du har skrevet gamle entity-ID-er direkte i egne YAML-kort eller automasjoner, oppdater dem til ID-ene i tabellen nedenfor.

Når **Automatisk laststyring** er på, eier automatikken strømgrensen. **Manuell ladestrøm** blir da utilgjengelig, og sensoren **Manuell styring** viser at skyveren er låst og at automatisk styring må slås av først. Forsøk på å skrive strømgrensen mens den er låst avvises også av integrasjonen. Når automatikken slås av, blir skyveren tilgjengelig igjen; Easee beholder siste dynamiske grense helt til en ny manuell grense sendes.

Smart Load Manager leser Easee-laderens status, strøm, spenning, faseinformasjon og strømgrenser. Den bruker HAN-effektmåleren og EnergyTariff sitt registrerte forbruk denne timen til å beregne en anbefalt dynamisk strømgrense. Integrasjonen kan sende grensen til Easee når du slår på **Automatisk laststyring**.

**Forbruksgrense** er én felles timegrense for installasjonen, ikke en separat grense per last. Den har samme valg som den tidligere `input_select.forbruksgrense`: 4,5–20 kWh i trinn på 0,5 kWh. Dette er en valg-entitet, ikke en målesensor. EnergyTariff leverer målt energi brukt hittil i timen; dens `target_energy` overstyrer ikke Forbruksgrense. Timeestimatet vises som diagnostikksensor. Easees maksimale strøm vises skrivebeskyttet.

Fasevalg tilbyr **Automatisk**, **Én fase** eller **Tre faser**. Valget sendes til Easee-integrasjonen. Det er adskilt fra sensoren for faktisk fasebruk. Sensorvisningsnavnene er korte og oversatt til norsk og engelsk.

Minimumsstrømmen følger den avtalte regelen, uten læring eller bilidentifikasjon:

- 11 A når Easee måler strøm på alle tre fasene under lading på 230 V IT/TT.
- 6 A ellers.

Fasebruk og spenning detekteres fra Easees målinger. Den målte spenningen brukes i beregningen, så noen volts variasjon endrer effektberegningen uten å starte noen ny innlæring.

Dette er beta-programvare. Den er ikke fysisk testet på din lader før du gjennomfører testen nedenfor. Integrasjonen er ikke en erstatning for vern, kurssikring eller Easees innebygde sikkerhetsfunksjoner.

## Forutsetninger

1. Easee-integrasjonen må være installert og laderen må være lagt til i Home Assistant.
2. EnergyTariff må være installert og konfigurert. Sensoren for **brukt energi denne timen** må være tilgjengelig i kWh.
3. Bruk samme HAN-effektsensor som EnergyTariff er satt opp med. Den må måle øyeblikkelig effekt i W eller kW, ikke energi i kWh.
4. Aktiver Easees diagnostiske strøm- og spenningssensorer hvis de er deaktivert.
5. Forbruksgrensen settes i Smart Load Manager etter oppsett. Den er en egen valg-entitet (select), ikke en målesensor, og erstatter den gamle `input_select.forbruksgrense`.

## Oppsett

Installer via HACS med prosjektets egendefinerte repository, eller kopier `custom_components/smart_load_manager` til Home Assistants `custom_components`-mappe. Start Home Assistant på nytt. Velg **Innstillinger → Enheter og tjenester → Legg til integrasjon → Smart Load Manager OJM**.

Velg Easee-enheten, HAN-effektsensoren, EnergyTariff-sensoren for brukt energi og sikkerhetsmargin. Etter oppsett finner du **Forbruksgrense** og **Fasevalg** blant kontrollene til Smart Load Manager. Forbruksgrensen er installasjonens felles timebudsjett. Oppsettet spør ikke etter timesestimat eller maksimal ladestrøm:

- Timesestimatet vises etter oppsett som sensor fra Smart Load Manager. Det er kun til sammenligning og er ikke et styringskrav.
- Easees maksimale strømgrense vises som en skrivebeskyttet sensor og brukes som øvre beregningsgrense.
- Hvis Easee ikke rapporterer en gyldig strømgrense, er anbefalingen 0 A og manuell positiv strømgrense sperres.
- Hvis en kilde mangler eller ikke har riktig enhet, viser oppsettet en forklaring og lar deg rette valget.

Forbruksgrensen og sikkerhetsmarginen lagres i integrasjonen. Du skal ikke lage egne `input_number`, `input_datetime` eller andre hjelpere.

## Sensorer og styring

Integrasjonen oppretter kontroller for Forbruksgrense, Fasevalg, automatisk laststyring, manuell ladestrøm og tidsstyring. Sensoroversikten viser blant annet laderstatus, rapportert modus, faktisk fasebruk, spenning, nettype, minste og anbefalt strøm, Easees maksstrøm, ladeeffekt, HAN-effekt, brukt energi, timeestimat, måleferskhet og styringsforklaring.

### Sensor-ID-er

| Entity-ID | Navn i Home Assistant |
|---|---|
| `sensor.slm_charger_status` | Ladestatus |
| `sensor.slm_charger_phase_mode` | Laderens fasevalg |
| `sensor.slm_output_phase` | Fase ut fra laderen |
| `sensor.slm_active_phases` | Faser i bruk |
| `sensor.slm_grid_type` | Strømnett |
| `sensor.slm_voltage_system` | Spenningssystem |
| `sensor.slm_line_voltage` | Spenning mellom faser |
| `sensor.slm_phase_neutral_voltage` | Spenning fase til nøytral |
| `sensor.slm_min_current` | Minste ladestrøm |
| `sensor.slm_recommended_current` | Anbefalt ladestrøm |
| `sensor.slm_max_current` | Maksimal ladestrøm |
| `sensor.slm_charger_current` | Strøm til bilen |
| `sensor.slm_charger_power` | Ladeeffekt |
| `sensor.slm_home_power` | Effekt fra strømmåleren |
| `sensor.slm_energy_used_hour` | Forbruk hittil denne timen |
| `sensor.slm_energy_estimate_hour` | Forventet forbruk denne timen |
| `sensor.slm_detection_confidence` | Sikkerhet i målingen |
| `sensor.slm_phase_detection_reason` | Fase- og spenningsgrunnlag |
| `sensor.slm_control_reason` | Hvorfor skjer dette? |
| `sensor.slm_manual_control_status` | Manuell strømstyring |
| `sensor.slm_charger_pause_reason` | Årsak til ladebegrensning |
| `sensor.slm_auto_control_status` | Automatisk laststyring status |
| `sensor.slm_meter_age` | Alder på måling |
| `sensor.slm_meter_valid` | Måling gyldig |
| `sensor.slm_schedule_active` | Tidsstyring aktiv |
| `sensor.slm_schedule_status` | Tidsstyring status |

**Automatisk laststyring** er avslått ved oppsett og etter Home Assistant-omstart. Når du slår den på, beregner integrasjonen på nytt hvert 30. sekund. Den sender anbefalt strøm når lading er tillatt, og sender 0 A når bilen er frakoblet, tidsvinduet er lukket, nødvendige kildedata er ugyldige/utdaterte eller det ikke finnes et pålitelig elektrisk grunnlag. Easee-grensen oppdateres når den endres og fornyes hvert femte minutt. `time_to_live: 0` gjør at siste kommando blir stående til den erstattes.

Beregningen bruker HAN-effekt minus laderens målte effekt for å anslå huslast. Den trekker EnergyTariff sitt forbruk hittil denne timen, forventet husenergi resten av timen og sikkerhetsmargin fra Forbruksgrense. Gjenværende energi omregnes til ampere med målt spenning og detektert fasebruk, og begrenses av Easees rapporterte maksimale strøm.

Når **Automatisk laststyring** slås av, stopper integrasjonen å sende nye automatiske kommandoer; Easee beholder siste dynamiske grense. **Manuell ladestrøm** er et bevisst alternativ når automatikken er av: skyveren sender dynamisk strømgrense til Easee, og 0 A betyr pause. Positive verdier kan ikke overstige Easees rapporterte grense eller være lavere enn detektert minimum. Slå på Automatisk laststyring igjen for at anbefalingen skal overta.

Endre Fasevalg når du er til stede og kan følge med. Kontroller både rapportert fasemodus og målte aktive faser etter endring. Fysisk respons må bekreftes i din egen Easee-installasjon.

### Tidsstyring

Integrasjonen har en egen bryter **Tidsstyring** og tidsentiteten **Starttid for lading** (standard 23:00). Når tidsstyring er på, tillates lading i et daglig 12-timersvindu fra starttidspunktet. Vinduet går over midnatt. Når tidsstyring er av, brukes timebudsjettet uten klokkeslettsperre. Tidsinnstillingene beholdes ved omstart; automatisk laststyring starter likevel avslått.

## Sikker test i en Home Assistant-instans som allerede styrer laderen

Testen lar din eksisterende løsning være urørt, bortsett fra at automasjonen midlertidig deaktiveres så den ikke konkurrerer med integrasjonen.

1. Ta en Home Assistant-sikkerhetskopi. Noter hvordan du reaktiverer den eksisterende automasjonen **Dynamisk styring av Easee-lader Opptimalisert V3.0**.
2. Deaktiver denne automasjonen før du sender strømgrenser med den nye integrasjonen. Ikke slett den, og ikke endre YAML-en.
3. Installer beta 14 og start Home Assistant på nytt. La **Automatisk laststyring** være av.
4. Kontroller oppsettskjemaet: det skal ikke be om EnergyTariff-estimat eller maksimal strøm. Etter oppsett bekrefter du at EnergyTariff-estimatet og Easees maksimale strøm vises som sensorer.
5. Mens automatisk styring fortsatt er av, sammenlign målt spenning, aktive faser, minste strøm, Easees maksimale strøm, HAN-effekt, EnergyTariff brukt energi og anbefalt strøm med Easee-appen og eksisterende målinger. Ingen dynamisk grense sendes i denne observasjonsfasen.
6. Når sensorene stemmer, aktiver automatisk styring mens du er til stede og følger med på laderen. Den gamle automasjonen skal fortsatt være deaktivert. Kontroller at anbefalingen og den rapporterte Easee-grensen følger hverandre, og at ladingen reagerer som forventet.
7. Ikke fremprovoser ugyldig måler eller lukket klokkevindu mens lading må fortsette. Disse tilfellene dekkes av automatiserte tester; en faktisk 0 A-pause kan testes separat når det er greit å avbryte ladingen.
8. For å gå tilbake: slå av **Automatisk laststyring** og reaktiver den gamle automasjonen. Den vil sende sin beregnede grense ved neste trigger. Ikke la begge styringene være aktive samtidig.

Hvis noe ikke stemmer: slå av automatisk styring, reaktiver den gamle automasjonen og send sensorverdier/logg før videre feilsøking. Beta 14 skal ikke aktivere automatisk laststyring etter omstart.

## Dashboard

`examples/lovelace/charging_view.yaml` er en komplett dashboard-visning med `type: sections`. Lim den inn i rå YAML-konfigurasjon for en visning, ikke i YAML-editoren for ett kort. For korteditoren bruker du `examples/lovelace/charging_card.yaml`, som er ett gyldig `vertical-stack`-kort. Begge eksemplene inneholder status, styringer, måleverdier og grafer. Sensor-ID-ene bruker `sensor.slm_*`.

## Verifisering og begrensninger

GitHub Actions kjører enhetstester for elektriske beregninger, valg av strømkommando og tjenestekallet som sender positiv strøm/0 A med `time_to_live: 0`. Den kompilerer integrasjonsmodulene, kontrollerer JSON og importerer oppsettmodulen i Home Assistant-runtime. Dette beviser ikke at en kommando er fysisk mottatt av laderen. Den kontrollerte HA-testen over er nødvendig for å validere samspillet med din Easee-installasjon.
