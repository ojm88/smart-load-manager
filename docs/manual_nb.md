# Smart Load Manager OJM – brukerveiledning

SLM tilpasser én eller to Easee-ladere til boligens timebudsjett. Når boligen trenger mer effekt, reduseres ladingen. Når det blir plass igjen, kan ladingen fortsette. Du trenger ingen egne hjelpere eller YAML-automasjoner.

[Oppsett](#oppsett-steg-for-steg) · [Betjening](#betjening) · [Dashboard](#dashboard) · [Feilsøking](#hvis-ladingen-venter)

## Før du begynner

- Installer og konfigurer [nyeste Easee-integrasjon](https://github.com/nordicopen/easee_hass/releases/latest). Easee v2026.11.0 krever **Home Assistant 2026.10.0 eller nyere**.
- **HAN-effekt** for hele boligen, i W eller kW.
- **Energi brukt denne timen**, i kWh, som nullstilles ved hver hele time. [EnergyTariff](https://github.com/epaulsen/energytariff) anbefales; tilsvarende måling fra for eksempel Tibber kan brukes. Spotpris, døgnforbruk og totalmåler kan ikke erstatte denne sensoren.
- Aktiver **Strøm/Current (A)** og **Spenning/Voltage (V)** på **hver** Easee-lader: Innstillinger → Enheter og tjenester → Easee → laderen → Entiteter. Vis deaktiverte entiteter, aktiver begge og vent på målte verdier. Ladeeffekten må også være tilgjengelig.
- Valgfritt: et **anslag på totalt forbruk i inneværende klokktime**, i kWh. Eksempler er EnergyTariff `energy_estimate_this_hour` og Tibber **Estimated consumption current hour**. Dette er bare informasjon; manglende estimat stopper ikke lading.

## Installasjon

Last ned ønsket [utgivelse](https://github.com/ojm88/smart-load-manager/releases), kopier `custom_components/smart_load_manager` til `config/custom_components/`, og start HA på nytt. Ved oppdatering erstatter du integrasjonsmappen og starter HA på nytt. Ta sikkerhetskopi før oppdatering.

Bruk Marketplace på **Home Assistant 2026.11 eller nyere**.

[![Åpne Smart Load Manager OJM i Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=ojm88&repository=smart-load-manager&category=integration)

Bruk knappen ovenfor som snarvei, eller legg til repoet fra Marketplace-menyen:

1. Åpne **Innstillinger → Marketplace → ⋮ → Custom repositories**.
2. Koble til GitHub hvis du blir bedt om det.
3. Lim inn `https://github.com/ojm88/smart-load-manager`, velg **Integration** og trykk **Add**.
4. Søk etter **Smart Load Manager OJM** i Marketplace og velg **Install**.

Ved førstegangsinstallasjon kan du gå rett til **Innstillinger → Enheter og tjenester → Legg til integrasjon** og velge **Smart Load Manager OJM**. Ved oppdatering av en allerede lastet integrasjon ber Home Assistant om omstart.

[Home Assistants veiledning for Marketplace-repoer](https://contributors.home-assistant.io/marketplace/guides/catalog/#the-link-to-your-repository)

## Oppsett steg for steg

1. Åpne **Innstillinger → Enheter og tjenester → Legg til integrasjon → Smart Load Manager OJM**.
2. Velg **Boligens effekt (HAN)** og **Energi brukt denne timen**. Velg timeestimat hvis du har det. Uten valg brukes `sensor.energy_estimate_this_hour` hvis den finnes.
3. Velg **Sikkerhetsmargin**. Standard er 0,3 kWh. Marginen reserveres fra timebudsjettet for måleforsinkelse og forbruksendringer; høyere margin gir mindre plass til lading.
4. Velg **Elbillading – Easee**, første lader og dens faktiske elektriske tilkobling fra tabellen nedenfor.
5. Fullfør med én lader eller legg til én til. Den andre listen viser bare ledige ladere. Avbryter du før fullføring, lagres ingen delvis installasjon.
6. Sett **Forbruksgrense** under **SLM – Boligen**. Kontroller målegrunnlag og verdier før du starter styringen.
7. Slå av eldre automasjoner som endrer de samme ladegrensene. Slå på **Automatisk laststyring** på hver lader SLM skal styre. Nye ladere starter med automatikk av.
8. Generer dashboardkortet som beskrevet nedenfor.

### Velg riktig tilkobling

| Valg | Brukes når laderen fysisk er tilkoblet |
| --- | --- |
| 230 V IT/TT – énfase | 230 V IT/TT, én ladefase |
| 230 V IT/TT – trefase | 230 V IT/TT, tre tilkoblede faser |
| 400/230 V TN – énfase | TN, én fase og nøytral |
| 400/230 V TN – trefase | TN, tre faser og nøytral |

Dette beskriver installasjonen; det endrer ikke koblingen eller låser spenningen til en nominell verdi. SLM bruker relevante målte Easee-spenninger. Velg ut fra kjent installasjon, ikke antall faser bilen bruker akkurat nå. Fasevalg vises bare ved fysisk trefasetilkobling. Ved usikkerhet må tilkoblingen avklares før automatisk styring aktiveres.

### Velg en realistisk forbruksgrense

**Forbruksgrense** gjelder hele boligen, inkludert lading, per klokktime. Valgene er 4,5–20 kWh, i trinn på 0,5. Eksempel: 10 kWh i én time tilsvarer 10 kW i gjennomsnitt, men er ingen øyeblikkelig effekt- eller sikringsgrense.

Velg ut fra vanlig husforbruk, nettleietrinn og ladebehov. Med 10 kWh grense og 0,3 kWh margin bruker SLM 9,7 kWh som budsjett. Dersom huset bruker nesten hele budsjettet, må lading vente. De to laderne deler samme ledige kapasitet. SLM kan bidra til lavere effekttopper, men garanterer ingen bestemt besparelse.

## Betjening

**SLM – Boligen** samler forbruksgrense, status, målegrunnlag, ladeoversikt og samlet ladeeffekt. Med to ladere vises også **Lademåte**. Under **Lading** har hver lader egne kontroller og målinger; det er ingen felles automatikkbryter.

| Kontroll | Hva den gjør |
| --- | --- |
| Automatisk laststyring | Regulerer denne laderen etter boligens budsjett. På/av-valget beholdes ved vanlig omstart, omlasting og oppdatering. |
| Automatikk av / Manuell ladestrøm | Når automatikk slås av, forespør SLM laveste gyldige manuelle ladestrøm. Du kan deretter velge manuell grense innenfor tillatte grenser. Pause, tidsvindu og nødvendige målinger gjelder fortsatt. Automatikk av er ikke en stoppknapp. |
| Ladepause | Sender 0 A. Slå av pause for ny vurdering av automatisk lading eller gjenopptakelse av manuell grense. Ny pause kan ikke aktiveres ved fullført/frakoblet lader; en eksisterende pause kan fortsatt oppheves. |
| Tidsstyring og starttid | Tillater lading i et daglig 12-timers vindu, for eksempel 23:00–11:00. Gjelder også manuell lading. Åpent vindu garanterer ikke kapasitet. Slå av tidsstyring for lading uten tidsvindu. |
| Fasevalg | Velg én fase, automatisk eller tre faser ved trefasetilkobling. Innstillingen sendes til Easee. SLM bytter ikke fasevalg automatisk. |
| Førsteprioritet | Med to ladere får én førsteprioritet. Bryterne følger hverandre. Dette er SLM-prioritet, ikke endring av Easees masterrolle. |

Manuell ladestrøm skjules i kortet når den ikke kan brukes, for eksempel ved automatikk på, aktiv pause, stengt tidsvindu eller manglende målinger. Bruk **Ladepause** for å stoppe, ikke 0 A i skyveknappen.

**Lad begge** deler ledig effekt mellom kvalifiserte ladere innenfor deres grenser. Hvis bare én får plass, går førsteprioriteten først. **Én om gangen** gir hele den ledige kapasiteten til den første kvalifiserte laderen; fullført lading, frakobling, pause eller stengt tidsvindu kan gi den andre tur.

SLM bruker minste ladestrøm 11 A ved målt 230 V trefaselading, ellers 6 A. Maksimum hentes fra Easee og tastes ikke inn i SLM. Bil og lader kan trekke mindre enn SLM tilbyr. Easees egne installasjons- og brukergrenser gjelder fortsatt, og Easee håndterer intern fordeling på sin kurs. SLM styrer tilbudet ut fra boligens budsjett og erstatter ikke elektriske vern.

## Slik reguleres ladingen

- **Målinger og anbefalt ladestrøm** beregnes ved kildeendringer. En kontroll hvert 30. sekund følger også tid og målingenes gyldighet.
- **Vanlige strømendringer** skjer hvert femte minutt. En uendret grense sendes normalt ikke på nytt.
- **Endring av boligens timegrense** utløser regulering med én gang. Målinger, ladepause og tidsvindu gjelder fortsatt.
- **Tilkobling, brukerbetjening, tidsgrenser og gjenopprettede målinger** vurderes straks. Nødvendig kapasitet og øvrige tillatelser må fortsatt være på plass.
- **Risiko for å bruke opp timebudsjettet** kan gi tidligere reduksjon etter 30 sekunder; ved akutt risiko reduseres det straks. Etter tidlig reduksjon holdes ordinær økning igjen i minst fem minutter.
- **To ladere:** Reell reduksjon på en aktiv lader må bekreftes med nye målinger før kapasitet flyttes. En kjent, ubrukt lader med 0 W og under 1 A hvilestrøm behøver ikke rapportere samme nullverdi på nytt.
- **Fullført lading:** `completed` med 0 W og under 1 A frigjør ubrukt kapasitet uten ordinære budsjettkommandoer til den fullførte laderen. En ny ladeforespørsel vurderes straks. Statusen sier ikke hvilken batteriprosent bilen har.

### Tilbudt ladestrøm og faktisk forbruk

Ved nye tilbud reserverer SLM hele den tilbudte effekten i prognosen. Etter tre minutter med stabilt, positivt forbruk kan prognosen og reservasjonen for etablert manuell lading bruke målt effekt + 100 W. Dermed reserveres ikke ubrukt tilbudt effekt unødvendig når bilen eller appinnstillinger begrenser forbruket.

En ferdig innlært observasjon beholdes gjennom midlertidige ladepauser i samme økt. Under venting reserveres fortsatt hele tilbudet; samsvarende positivt forbruk ved gjenopptakelse kan gjenbruke observasjonen uten tre nye minutter. Fullført økt, frakobling og ugyldige målinger nullstiller den. Endret fasegrunnlag, automatikk/manuell-modus, endret forbruk eller tilbud over det observerte krever ny vurdering. Observasjonen lagres ikke gjennom omstart.

Dette er en forbruksprognose, ikke en innlært elektrisk maksimumsgrense. Skjulte appgrenser behøver ikke kopieres til SLM. Måleforsinkelser og raske forbruksendringer kan fortsatt gi kortvarige avvik.

## Målinger

| Måling | Betydning |
| --- | --- |
| Ladestatus | Easees rapporterte status: lader, venter, fullført eller frakoblet. |
| Effekt til bilen | Målt ladeeffekt i W. |
| Målt ladestrøm | Strømmen Easee måler til bilen, i A. |
| Anbefalt ladestrøm | Grensen SLM anbefaler nå. Kan avvike fra sist sendte grense frem til regulering; den er ikke målt forbruk. Minimum og rapportert maksimum finnes i attributtene. |
| Faser i bruk / Volt | Faktisk fasebruk og spenning fra relevante terminalmålinger. TN kan fortsatt være 400/230 V selv om bilen lader på én fase. |
| Status for laststyring | Samlet forklaring og korte, egne årsaker for hver lader. |
| Målegrunnlag | Om nødvendige kilder er gyldige, med kilde-ID-er og HAN-alder i attributtene. |
| Lading / Samlet ladeeffekt | Skrivebeskyttet ladeoversikt og summen av målt ladeeffekt, også fra manuelt styrte ladere. Manglende måling gir ukjent total, ikke 0 W. |

## Dashboard

1. Åpne **Innstillinger → Verktøy (Tools) → Handlinger (Actions)**.
2. Kjør:

   ```yaml
   action: smart_load_manager.get_dashboard
   data: {}
   ```

3. Kopier verdien i **`yaml`** fra svaret.
4. Rediger dashboardet, legg til et **Manuelt kort** i en eksisterende seksjon og lim inn YAML-en.

Generatoren bruker registrerte entitets-ID-er og ladernavn, også ved egne navn. Begge ladere får navn i grafens **Anbefalt ladestrøm** og **Målt ladestrøm**. Statuskortet er alltid norsk, også på en engelskspråklig HA-server; øvrige HA-entiteter følger serverens språk. Statiske [ett-lader](../examples/lovelace/charging_card.yaml)- og [to-lader](../examples/lovelace/two_chargers_card.yaml)-eksempler er maler som må tilpasses.

Kortet viser boligens målinger og budsjett først, deretter hver lader med status, Auto/Manuell og relevant forklaring. Det skiller mellom **kapasitetsmangel**, **positiv anbefaling som venter på regulering**, og **positiv grense sendt til en lader som fortsatt venter**. Ved kapasitetsmangel vises minste nødvendige effekt og råd om å redusere annet forbruk. Neste ordinære vurdering er ikke en garantert ladestart. Når ingen biler er tilkoblet, er visningen kortere.

Grafene viser ladestrøm og valgte energi-/estimatsensorer de siste 12 timene. **Snitt 3-timer** bruker `sensor.average_peak_hour_energy` hvis den finnes; ellers kan den raden fjernes fra kortets YAML. Estimatet kan avvike fra SLMs anbefaling fordi det er informasjon fra en separat kilde.

**Generer kortet på nytt** etter endring av laderantall, ladernavn, fysisk tilkobling, målekilder, refererte entitets-ID-er eller kortoppsett. YAML-en oppdateres ikke automatisk. Vanlig betjening av budsjett, prioritet, ladestrøm, fasevalg, pause og tidsstyring krever ikke ny YAML. Ta vare på egne korttilpasninger før du erstatter den. Hent nytt kort ved oppdatering til beta 22.

## Endre oppsettet senere

Åpne **Innstillinger → Enheter og tjenester → Smart Load Manager OJM → Konfigurer**.

- **Boligens målekilder og sikkerhetsmargin:** Endre HAN, brukt timeenergi, valgfritt estimat og margin. Kilder valideres før lagring; laderinnstillinger beholdes.
- **Ladere og tilkobling → Legg til lader:** Velg én ledig Easee-lader. Eksisterende lader og innstillinger beholdes; maks to ladere.
- **Fjern lader:** Tilgjengelig med to ladere. SLM sender 0 A til valgt lader før den fjernes; feil ved kommandoen avbryter endringen. Innstillinger beholdes ved senere gjeninnlegging.
- **Ladernes tilkobling:** Rett fysisk tilkobling ved behov. Valgt lader får 0 A og automatikk av før omlasting. Kontroller valget og aktiver styringen igjen når grunnlaget er riktig.

En vellykket 0 A-kommando er ikke i seg selv en målt bekreftelse på fysisk stopp. Vanlig omstart og oppdatering beholder automatikk, manuell innstilling, pause, tidsstyring og boligens valg. Easee lagrer fasevalget.

Hvis Easee fremdeles melder lading med ferske målinger 60 sekunder etter at SLM ba om 0 A, forsøker SLM én separat pausekommando. SLM gjenopptar sin egen reservepause først når ferske målinger viser stopp og styringen tillater lading igjen.

## Hvis ladingen venter

| Det kortet viser | Hva du kan gjøre |
| --- | --- |
| Venter på kapasitet | Se minste nødvendige ladeeffekt. Reduser annet forbruk eller vent til det blir plass. Velg et realistisk timebudsjett. |
| Venter på regulering | En ny anbefaling er beregnet, men laderen står fortsatt på tidligere grense. Se tidspunktet for neste ordinære vurdering. |
| Positiv grense sendt, men Easee venter | SLM har tilbudt strøm. Kontroller bilens ladeplan, ladegrense og eventuelle Easee-begrensninger hvis dette vedvarer. |
| Avventer målinger | Åpne Målegrunnlag. Kontroller HAN, brukt timeenergi, Easee-strøm/spenning/effekt og rapportert maksimum. |
| Avventer reduksjon | SLM venter på nye strøm-/effektmålinger før kapasitet kan overføres. Ved vedvarende venting: last ned diagnostikk. |
| Venter på starttid / Pauset | Kontroller laderens tidsvindu eller slå av Ladepause. |
| Manuell styring | Automatikk er av på denne laderen. Aktiver den hvis SLM skal regulere automatisk. |

Gyldige HAN-rapporter godtas til og med 120 sekunders alder, også når samme verdi rapporteres på nytt. Ved manglende/ugyldige rapporter sendes en stoppkommando til berørte styrte ladere. Gyldige målinger gir ny vurdering straks. En uendret, tilgjengelig Easee-effektmåling blir ikke ugyldig bare fordi tidsstempelet er gammelt.

### Last ned diagnostikk

Åpne integrasjonsoppføringen → **⋮ → Last ned diagnostikk** mens problemet er aktuelt, før omstart eller omlasting. Oppgi tidspunkt, versjon, forventet og faktisk oppførsel i [feilrapporten](https://github.com/ojm88/smart-load-manager/issues).

Filen viser anonyme målinger, beslutninger, effektreservasjoner og kommandoresultater. De siste 4096 hendelsene holdes i minnet; ved omstart/omlasting slettes historikken. Ingen bestemt tidsperiode er garantert. Vellykket tjenestekall er ikke bevis på fysisk lading.

## Avgrensninger

SLM er under utvikling. Se [teststatus](PROJECT_STATUS.md) for hva som er programvaretestet og fysisk bekreftet. Systemet optimaliserer ikke etter spotpris, styrer ikke bilens batteriprosent og erstatter ikke sikringer eller Easees interne begrensninger. Varmtvann og gulvvarme er planlagt, men ikke implementert.
