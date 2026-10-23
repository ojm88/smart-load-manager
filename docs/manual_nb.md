# Brukermanual — Smart Load Manager OJM beta.11

## Hva beta 11 gjør

Smart Load Manager leser Easee-laderens status, strøm, spenning, faseinformasjon og strømgrenser. Den bruker HAN-effektmåleren og EnergyTariff sitt registrerte forbruk denne timen til å beregne en anbefalt dynamisk strømgrense. Integrasjonen kan sende grensen til Easee når du slår på **Automatisk laststyring**.

**Forbruksgrense** er én felles timegrense for installasjonen, ikke en separat grense per last. Den har samme valg som den tidligere `input_select.forbruksgrense`: 4,5–20 kWh i trinn på 0,5 kWh. Dette er en valg-entitet, ikke en målesensor. EnergyTariff leverer målt energi brukt hittil i timen; dens `target_energy` overstyrer ikke Forbruksgrense. Timeestimatet vises som diagnostikksensor. Easees maksimale strøm vises skrivebeskyttet.

Beta 11 legger til **Fasevalg**: Automatisk, Én fase eller Tre faser. Valget sendes til Easee-integrasjonen. Det er adskilt fra sensoren for faktisk fasebruk. Sensorvisningsnavnene er gjort kortere og oversatt til norsk og engelsk.

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
3. Installer beta 11 og start Home Assistant på nytt. La **Automatisk laststyring** være av.
4. Kontroller oppsettskjemaet: det skal ikke be om EnergyTariff-estimat eller maksimal strøm. Etter oppsett bekrefter du at EnergyTariff-estimatet og Easees maksimale strøm vises som sensorer.
5. Mens automatisk styring fortsatt er av, sammenlign målt spenning, aktive faser, minste strøm, Easees maksimale strøm, HAN-effekt, EnergyTariff brukt energi og anbefalt strøm med Easee-appen og eksisterende målinger. Ingen dynamisk grense sendes i denne observasjonsfasen.
6. Når sensorene stemmer, aktiver automatisk styring mens du er til stede og følger med på laderen. Den gamle automasjonen skal fortsatt være deaktivert. Kontroller at anbefalingen og den rapporterte Easee-grensen følger hverandre, og at ladingen reagerer som forventet.
7. Ikke fremprovoser ugyldig måler eller lukket klokkevindu mens lading må fortsette. Disse tilfellene dekkes av automatiserte tester; en faktisk 0 A-pause kan testes separat når det er greit å avbryte ladingen.
8. For å gå tilbake: slå av **Automatisk laststyring** og reaktiver den gamle automasjonen. Den vil sende sin beregnede grense ved neste trigger. Ikke la begge styringene være aktive samtidig.

Hvis noe ikke stemmer: slå av automatisk styring, reaktiver den gamle automasjonen og send sensorverdier/logg før videre feilsøking. Beta 11 skal ikke aktiveres automatisk ved omstart.

## Dashboard

`examples/lovelace/charging_view.yaml` er et eksempel med standard Home Assistant-kort. Det viser kontrollene, anbefalt strøm, minste strøm, Easees maksimale strøm, elektrisk deteksjon og EnergyTariff-sensorene. Bytt plassholdernes entity-ID-er med entity-ID-ene HA opprettet for din Smart Load Manager-enhet før du legger YAML-en inn i et dashboard.

## Verifisering og begrensninger

GitHub Actions kjører enhetstester for elektriske beregninger, valg av strømkommando og tjenestekallet som sender positiv strøm/0 A med `time_to_live: 0`. Den kompilerer integrasjonsmodulene, kontrollerer JSON og importerer oppsettmodulen i Home Assistant-runtime. Dette beviser ikke at en kommando er fysisk mottatt av laderen. Den kontrollerte HA-testen over er nødvendig for å validere samspillet med din Easee-installasjon.
