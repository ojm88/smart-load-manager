# Læring fra 0.1.1-beta.1–15

Gjennomgått 2026-10-29 etter eiers tilbakemelding. Omfanget er de 15 betaene
etter stabil 0.1.0: utgivelsesnotater, beslutningslogg, eierens observerte
forløp og relevante kontroll-/testfiler. Dette er en årsaksanalyse av utviklingen,
ikke en ny fysisk aksepttest eller en garanti om feilfri nåværende kode.

## Hovedkonklusjon

For mange avklaringer og feil ble oppdaget av eieren etter publisering. En
vesentlig del var forutsigbar ved å undersøke datakontrakten, hele ladeforløpet,
plattformens navigasjon og vanlige tom-/mobiltilstander tidligere. Eieren skal
primært teste det som faktisk krever hans bil, lader og installasjon, ikke være
første kontroll av normal programvarelogikk og kortets grunnleggende brukbarhet.

Flere betaer inneholdt også bestilte utvidelser. Antall versjoner er derfor
ikke et mål på antall feil, og vi kan ikke etterpå gi et troverdig eksakt tall
på hvor mange utgivelser som kunne vært spart. Problemet var gjentatte
utgivelser for samme brukerbehov uten tilstrekkelig helhetskontroll.

## Gjennomgang av hver beta

| Beta | Endring / erfaring | Hva jeg burde gjort tidligere |
| --- | --- | --- |
| 1 | Navnet Ladeforklaring og tydelig sensorbeskrivelse. | Se gjennom alle brukertekster samlet mot den eksisterende fungerende automasjonen og kortet. En legitim presentasjonsendring, ikke dokumentert laderegresjon. |
| 2 | Prosjektforklaring, nettleie, avgrensning og nøytrale statusmeldinger. | Samle språk/produktforklaring i en gjennomarbeidet presentasjonsrunde. Nye ønsker må skilles fra feil. |
| 3 | To ladere, felles budsjett, prioritet, fordelingsmåter og kortgenerator. | Utarbeide en-/to-lader-forløp og akseptkrav før utvidelsen: én fungerende lader er en regresjonsreferanse; to kontrollere er en ny koordinert tilstandsmaskin. |
| 4 | Bedre måle-/ventehåndtering og fjerning av 120-sekunders cutoff for ladeeffekt. | Undersøke hvilke Easee-data som rapporteres ved endring. Uendret effekt er ikke i seg selv foreldet. Skille dette fra HAN-ferskhet og kravet om nye rapporter etter reduksjon. |
| 5 | Omlegging til én installasjon, grupper, identiteter og medlemskap. | Teste virkelig førsteoppsett → legg til → reload → fjern → legg til igjen, inkludert avbrudd, før publisering. Bevaring av første lader må være et uttrykkelig krav. |
| 6 | Rettet tillegg som erstattet eksisterende lader, unload og utilgjengelige sensorer; raskere liste. | Dette var i stor grad oppdagbar programvare-/livssykluslogikk, ikke avhengig av fysisk lading. Backend-medlemskap og frontend-ytelse måtte undersøkes hver for seg. |
| 7 | Egen sammenligningsside for logovalg. | Avklare hva et slikt eksperiment faktisk beviser. En rask separat side beviser ikke at samme løsning virker i oppsettdialogen eller Companion. Ikke introdusere synlig testnavigasjon uten at den inngår i ønsket produktflyt. |
| 8 | Kobling til logovalg via ekstern flyt; rydding av sidemeny og README. | Verifisere in-app-kravet før ekstern navigasjon ble del av oppsettet. Gjøre vanlige menyvalg, tillegg og avbrudd ferdige samlet. |
| 9 | Rettet duplikat/tomt menyvalg og relative URL-er. | Teste ekte publisert skjema med alle menytekster, konfigurerte Cloud-URL-er og åpneknapp. Absolutt URL løste ikke det overordnede Companion-kravet. |
| 10 | Native logoer i oppsettdialogen. | Undersøke støttet HA-enhetsvelger og frontendens filtrering/preseleksjon tidligere. Flere av logo-iterasjonene kunne trolig vært unngått; faktisk telefonhastighet krevde fortsatt eierens test. |
| 11 | Bekreftet fysisk IT/TT/TN-tilkobling og faseantall; relevante målte spenninger. | Slutte å behandle høyeste terminalpar eller antall fylte attributter som bevis på installasjonen. Skille nettype, fysisk tilkobling, valgt fasemodus og målte aktive faser. Avklare manglende entydig nettype før automatisk konklusjon. |
| 12 | Live målinger/anbefaling, femminutters kommandoer og tidlige reduksjoner; statusdekning. | Da intervallet ble endret, følge alle start/stopp-forløp og asynkron datalevering. Ikke blande visning av completed med beslutningen om å sende pause. Testene beskrev delvis den implementerte antakelsen, ikke ønsket komplett forløp. |
| 13 | Rettet stopp når charging kom før strømmålinger; straksstart ved innplugging. | Modellere status-før-strøm, strøm-før-status og forsinket HAN allerede før beta 12. Umiddelbar vurdering ved tilkobling er en naturlig konsekvens av femminuttersmodellen, selv om ønsket ble presisert senere. |
| 14 | Straksrespons på betjening/tidsgrenser og rettet completed/pause-sløyfe. | Gjennomgå hele ladeøkten og alle eksplisitte startårsaker sammen med beta 12. Dokumentere at 0 A er en fysisk pausekommando som kan gi ny status; fullført må ikke automatisk bety pause. Nye/målte data etter kommando og fornyet forbruk må fortsatt tas med. |
| 15 | Kompakt mobilkort, tomtilstander og relevant informasjon etter tilkobling/lading. | Vise kortet med ingen/én/to biler, venting, ferdig lading, lange navn og høye tall på smal skjerm fra starten. Dette trengte ikke en full ladeøkt for å bli oppdaget. Strukturelle maltester er ikke en måling av faktisk iPhone-layout. |

## Hvorfor mange grønne tester ikke var nok

Et konkret eksempel finnes i beta 12: testen
`test_finished_charger_stops_without_raising_peer_before_tick` forventet at
`completed` skulle gi en 0 A-kommando. Det var en test av vår beslutning, ikke
av om beslutningen ga riktig atferd hos Easee gjennom neste statusovergang.

Den manglende kjeden var: bilen avslutter → SLM sender pause → Easee melder
venting/klar → SLM behandler dette som nytt ladebehov → ny strømgrense → ny
avslutning. Et krav om null anbefaling i kortet ble koblet for direkte til en
fysisk styringskommando. Flere tester av enkeltstatuser kunne derfor være
grønne samtidig som forløpet var feil.

En annen mangel var at syntetiske eksempler ofte hadde samstemt status, strøm
og effekt. Virkelige kilder kommer i ulik rekkefølge. Koden måtte tåle
`charging` med foreløpig 0 A uten å miste den allerede validerte elektriske
modellen. Det er en forutsigbar asynkron situasjon, selv om akkurat eierens
observasjon kom fra fysisk testing.

Testantall skal oppgis som omfang, aldri som et mål på sannsynlighet for at
produktet virker. Det avgjørende er hvilke feilforløp testene faktisk utelukker,
hvor mye som er mock-et, og hva som ennå ikke er bekreftet.

## Arbeidsmåte videre

1. Beskriv brukerens hele forløp og hva som allerede virker før implementasjon.
   Noter berørte og uberørte deler, forventet status, tidskrav og forventede
   kommandoer. Undersøk nødvendige Easee-/HA-kilder før antakelser blir kode.
2. Opprett en liten faktaoversikt for hver kilde: betydning, enhet, terminal,
   rapporteringsmåte, manglende verdi, ukjent enum og hva som er bekreftet.
   Ikke gjett elektrisk topologi fra tvetydige målinger. Spør om avgjørende
   uklarheter som tilgjengelige kilder ikke kan avklare.
3. Vurder konsekvensene av hver kommando: hva kan endres i laderen, hvilken
   tilbakemelding kan komme, og kan den utløse samme kommando igjen? Skill
   anbefalt grense, sist sendt grense, målt forbruk og bilens behov.
4. Velg tester fra brukerkravet og en feilmekanisme, ikke ved å kopiere den nye
   implementasjonen. Test relevante hele sekvenser med forskjellige
   kildeordener, tidsgrenser, forsinkede svar og én/to ladere. Behold en
   regresjonsreferanse for den eksisterende fungerende installasjonen.
5. For UI-endringer: kontroller generert kort og faktisk render, ikke bare
   enkeltstrengene. Bruk smale visningsflater, høye tall, lange navn og tomme/
   utilgjengelige/ventende/fullførte tilstander. Avtal faktisk telefonaksept
   bare for det vi ikke kan verifisere lokalt; oppgi hva som mangler.
6. Før en utgivelse: sammenhold diffen med ønsket omfang, samle allerede
   avtalte og sammenhengende forbedringer, og beskriv uavklarte forhold
   konkret. En grønn CI erstatter ikke funksjonsvurdering. Ved kritisk uavklart
   oppførsel: undersøk først, ikke presenter en antakelse som ferdig løsning.
7. Lag en kort målrettet ladetest for eieren etter softwarekontrollen: hvilken
   installasjon/forbindelse, hvilken handling og hvilket observerbart resultat.
   Ikke la ham gjenta unødvendige grunnkontroller på hver beta.
8. Oppdater én tydelig nåstatus og en kort beslutning når noe endres. Skill
   historiske klargjøringsnotater fra faktisk publisert versjon og fjern
   motstridende nåtidsformuleringer. Ikke omskriv README eller kjør tunge
   runtime-suiter bare fordi interne prosessnotater ble endret.

Dette endrer ikke eiers rett til å bestille små betaer raskt. Ingen ekstra
bekreftelsesrunde innføres for ordinært utviklingsarbeid. Publisering og
installasjon følger fortsatt den autorisasjonen eieren faktisk har gitt.

## Sjekkmatrise for endringer i ladestyringen

Bruk relevante rader etter endringens påvirkning; det kreves ikke alle
kombinasjoner eller nye tester for rent kosmetiske endringer.

| Forløp | Det som må være avklart / undersøkt |
| --- | --- |
| Innplugging og oppstart | Straksvurdering når tillatt; status før strøm og motsatt; ikke stoppe på et legitimt overgangsbilde. |
| Tidsstyring og betjening | Nøyaktig åpning/lukking også uten nye kildedata; pause/resume; automatikk/manuell; kontrollene må ikke arve ordinær femminuttersventing utilsiktet. |
| Fullført og ny bruk | Ikke sende unødvendige pause-/startsløyfer; råstatus er ikke batteriprosent; eventuell beholdt grense reserveres; faktisk oppvåkning/forvarming må aksepteres fysisk. |
| To ladere | Aktiv kontra avsluttet økt, ulike kW/A-faktorer, begge fordelingsmåter, prioritet, ny tilkobling/frakobling og målt reduksjon før økning. |
| Elektrisk modell | IT/TT og TN, fysisk én/tre fase, valgt modus og målt fasebruk hver for seg; relevante målte terminalverdier, lav spenning og manglende data. |
| Kilder og feil | Uendret men gyldig verdi, endring av bare attributter, separat HAN-ferskhet, ukjent status, forsinkelse/feil i kommando, kildeendring under ventende kommando. |
| Installasjonslivsløp | Førsteoppsett, avbrudd, additive valg, reload, fjerning og gjenoppretting; identiteter og brukerinnstillinger bevares. |
| Presentasjon | Ingen/én/to biler, charging/waiting/completed/fault, reelle navn, manglende tall, smal skjerm og høyere tekststørrelse; nytt YAML når layout endres. |

## Det som fortsatt krever fysisk bekreftelse

Den faktiske bilens og laderens overgangstider, minstekrav, oppvåkning,
forvarming og stabilitet over en ladeøkt må bekreftes på utstyr. To-lader-
forløp og telefonens faktiske ytelse/rendering har egne akseptkrav. Vi kan og
skal undersøke langt mer av programvaren først, uten å late som dette gjør
fysisk testing overflødig. Ingen ny fysisk aksept er gjennomført i denne runden.

## Sporbare kilder i prosjektet

- [Endringslogg](../CHANGELOG.md): alle 0.1.1-beta.1–15.
- [Beslutninger](DECISIONS.md): særlig endringsbasert effekt, Companion,
  bekreftet elektrisk tilkobling, live beregning og completed/pause.
- [Arkitektur](ARCHITECTURE.md): måling, beregning, kommando og presentasjon.
- [Beta 12-test som forventet pause ved completed](https://github.com/ojm88/smart-load-manager/blob/118bc974c8915c830893503e112cc3a5c4fa1c9d/ha_tests/test_site_runtime.py#L257).
- [Medlemskapstester](../ha_tests/test_membership_runtime.py),
  [kontrollhendelser](../ha_tests/test_control_events_runtime.py),
  [reguleringsforløp](../ha_tests/test_site_runtime.py),
  [korttester](../ha_tests/test_dashboard_runtime.py).
