# Brukermanual — Smart Load Manager beta.4

## Hva betaen gjør

Beta.4 leser målinger fra Easee, HAN-måleren og EnergyTariff, viser hvordan Easee-fasene tolkes, beregner en anbefalt ladestrøm og kan sende en dynamisk strømgrense til Easee. Den har kontroll av HAN-målingens alder og valgfri tidsstyring. Automatisk styring er avslått ved første oppstart og etter omstart av Home Assistant. Denne versjonen styrer ikke varmtvannstank eller varmekabler.

Dette er fortsatt en beta. Den er ikke validert mot en fysisk Home Assistant-instans eller lader. Kontroller sensorene og anbefalingen før du aktiverer automatisk styring.

## Før installasjon

1. Installer og konfigurer Easee-integrasjonen.
2. Installer og konfigurer EnergyTariff. Kontroller at `energy_used_this_hour` og `energy_estimate_this_hour` viser tilgjengelige, numeriske verdier.
3. Sørg for at HAN-effektsensoren er den samme effektsensoren EnergyTariff bruker. Enheten må være W eller kW, ikke kWh.
4. Aktiver Easees diagnostiske strøm- og spenningssensorer fra Easee-enhetens integrasjonsinnstillinger.
5. Sammenlign EnergyTariff sin `target_energy` med timegrensen du legger inn i Smart Load Manager.

## Installasjon

Kopier mappen `custom_components/smart_load_manager` til Home Assistants `custom_components`-mappe, eller installer gjennom HACS dersom du selv har lagt prosjektet i et HACS-kompatibelt GitHub-repository. Start Home Assistant på nytt. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon** og velg **Smart Load Manager**.

I oppsettskjemaet velger du Easee-lader, HAN-effekt, EnergyTariff-sensor for brukt energi, EnergyTariff-estimat, timegrense, øvre strømgrense og sikkerhetsmargin. Sett øvre strømgrense konservativt; integrasjonen tar også hensyn til positive kurs-/ladergrenser den finner i Easee-attributtene.

Tidsstyring er valgfri. For samme oppsett som den tidligere automasjonen velger du `switch.easee_smartlading` som tidsstyringsbryter og `input_datetime.smartlading_starter_kl` som starttid. Entity-ID-ene kan hete noe annet i din installasjon; velg dem fra listene i oppsettskjemaet.

Har du allerede installert en tidligere beta, åpner du integrasjonens **Konfigurer**-valg og velger tidsstyringsbryter og klokkeslett der. Du trenger ikke slette integrasjonen.

Hvis du ikke har en starttid-hjelper ennå: gå til **Innstillinger → Enheter og tjenester → Hjelpere → Opprett hjelper → Dato og/eller tid**. Velg kun klokkeslett, uten dato, og gi den for eksempel navnet **Smartlading starter kl**. Velg denne `input_datetime`-entiteten i Smart Load Manager-oppsettet.

Alternativt kan du opprette den i en YAML-pakke:

```yaml
input_datetime:
  smartlading_starter_kl:
    name: Smartlading starter kl
    has_date: false
    has_time: true
```

Dette er en klokkeslett-hjelper, ikke en målesensor. Velg den opprettede `input_datetime.smartlading_starter_kl` i oppsettet.

## Easee-data og fasetolkning

Pakken finner Easee-sensorer som tilhører den valgte enheten; du skal ikke skrive inn `sensor.easee_*`-navn manuelt. Sensorattributter leses etter feltnavn, og Easee-enum-kodene tolkes innenfor hvert sitt kodefelt.

- `config_phaseMode`: 1 = låst én fase, 2 = automatisk, 3 = låst tre faser.
- `state_outputPhase`: faktisk Easee-utgangskonfigurasjon. Koder 10–15 er énfase, 20–22 er tofase og 30 er trefase TN. Den dekodede teksten vises separat fra fasemodusen.
- `config_detectedPowerGridType`: når tilgjengelig, viser Easees nettypekode (blant annet TN 1/2/3-fase og IT 1/3-fase).
- Terminalstrømmer og terminalspenninger brukes til å beregne faktisk aktiv fasebruk og spenningsklasse. Integrasjonen baserer seg ikke bare på gjennomsnittssensoren «Spenning».
- `state_reasonForNoCurrent` vises som separat forklaring. Samme numeriske verdi i et annet enum-felt har ikke nødvendigvis samme betydning.

Avtalt nedre strømgrense: 230 V med tre aktive faselederstrømmer gir 11 A; ellers 6 A. Klassifiseringen følger målt spenningsklasse og faktisk fasebruk, ikke et manuelt IT/TT-valg. Hvis sensorer mangler, er ukjente eller gir motstridende data, sender automatisk styring 0 A.

## Styring

### Automatisk laststyring

Slå på `Automatisk laststyring` først når diagnostikksensorene er kontrollert. Den er av som standard og blir av igjen etter omstart. Når den er aktiv, beregnes strømgrensen hvert 30. sekund. Easee mottar bare en ny kommando når anbefalingen endres, og kommandoen fornyes minst hvert femte minutt. Kommandoen bruker `time_to_live: 0`, som i Easee-integrasjonen betyr at grensen gjelder inntil en ny dynamisk grense sendes.

Beregningen trekker målt ladeeffekt fra HAN-effekten for å anslå huslasten, estimerer resterende husenergi i timen, trekker fra forbrukt EnergyTariff-energi og sikkerhetsmargin, og regner tilgjengelig energi om til ampere med gjeldende målte spenning/fasekonfigurasjon. Dersom tilgjengelig strøm blir lavere enn tillatt minimum, anbefales 0 A i stedet for en ugyldig strøm under grensen.

### Manuell ladestrømgrense

`Manuell ladestrømgrense` sender en grense via Easee-integrasjonens `easee.set_charger_dynamic_limit`. 0 A betyr pause. En positiv verdi under den detekterte minimumsgrensen avvises. Slå av automatisk styring før manuelle endringer. Easee beholder grensen til den erstattes av en ny dynamisk grense; dette endrer ikke laderens installerte maksstrøm.

### Tidsstyring

For å bruke tidsplanen må både `Automatisk laststyring` og den valgte Easee Smartlading-bryteren være på. Førstnevnte aktiverer strømstyringen; Easee-bryteren slår klokkevinduet av eller på. Når Easee-bryteren er **av**, følger ladingen timebudsjettet uten et klokkeslettvindu. Når den er **på**, tillates lading fra starttiden i `input_datetime` og de neste 12 timene. Etter tidsvinduet sender aktiv automatisk styring 0 A. Vinduet fungerer over midnatt og gjentas daglig. Tidsstyringssensorene viser om vinduet er aktivt og hvorfor.

HAN-måleren må vise positiv effekt, og selve sensorverdien må ha endret seg i løpet av de siste 60 sekundene. Hvis verdien ikke endres, blir utilgjengelig eller er 0, sender aktiv automatisk styring 0 A. Dette følger samme `last_changed`-vakt som automasjonen din. Når måleren igjen oppdateres med gyldig verdi, beregnes ladestrømmen på nytt.

## Dashboard

Importer eller kopier `examples/lovelace/charging_view.yaml` inn i en ny Lovelace-visning. Kortet bruker standard HA-kort. Erstatt markerte eksempel-entity_id-er med entitetene som ble opprettet for din lader og de EnergyTariff-sensorene du valgte. Ikke lim inn kortet i den eksisterende produksjonsvisningen før entitetene er kontrollert.

## Første test

1. La automatisk styring være av. Kontroller at status, valgt fasemodus, faktisk utgangsfase, aktive faser, spenning, strømgrense og beregnet anbefaling stemmer med Easee-appen og målingene.
2. Kontroller at HAN-sensorens enhet er W eller kW, at effektsensoren måler totalforbruket, og at EnergyTariff-sensorene viser riktig time.
3. Prøv manuelt å sette 0 A mens du følger med på at ladingen pauses. Gjenoppta ved å sette en verdi som er minst anbefalt minimum og innenfor strømgrensen.
4. Kontroller at HAN-målingens alder er under 60 sekunder og at gyldighetssensoren viser Ja. Hvis tidsstyring brukes, test med den av først og bekreft starttid og tidsvindu før du slår den på.
5. Først etter dette kan du aktivere automatisk styring mens du følger anbefalingen, HAN-effekten, Easee-strømmen og EnergyTariff-verdiene.
6. Slå av automatisk styring hvis verdier blir ukjente eller ikke samsvarer med målingene. Når den er av, slutter integrasjonen å sende nye grenser, men Easee beholder siste dynamiske grense inntil en ny grense erstatter den. Sett ønsket manuell grense eller aktiver automatisk styring igjen.

Deaktiver den gamle automasjonen **Dynamisk styring av Easee-lader Opptimalisert V3.0** før du slår på automatisk styring i Smart Load Manager. Begge styringene bruker samme Easee-tjeneste og kan ellers sende ulike strømgrenser.

## Feilsøking og begrensninger

- Oppsettet feiler hvis de valgte kildeentitetene ikke er tilgjengelige/numeriske eller hvis HAN-sensoren ikke er W/kW.
- Hvis Easees strøm-/spenningssensorer er deaktivert, aktiver dem og last integrasjonen på nytt.
- «Ukjent» fase eller spenning betyr at pakken ikke har nok pålitelige data; automatisk styring sender da 0 A.
- Betaen oppdager kompatibilitet via tilgjengelige Easee-entiteter og attributter, ikke en full sertifisering av alle lademodeller.
- EnergyTariff-estimat vises for sammenligning. Den foreløpige beregningen bruker målt HAN-effekt minus Easee-effekt for å anslå huslasten, siden estimatet kan inkludere elbillading.
- Testene dekker beregningsfunksjoner, ikke oppstart i HA, ekte Easee-svar eller fysisk lading. Ikke bruk betaen som eneste elektriske beskyttelse eller sikringsvern.
