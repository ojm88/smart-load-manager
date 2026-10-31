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
3. Velg elbillading, første Easee-lader og laderens fysiske tilkobling. Velg deretter å fullføre med én eller legge til en til. Listen for lader to viser bare enheter du ikke allerede har valgt.
4. Velg **Forbruksgrense** på **SLM – Boligen** (4,5–20 kWh per time, trinn på 0,5).
5. Slå av eventuell tidligere automasjon som regulerer de samme laderne. Slå deretter på automatisk laststyring for laderne du vil styre.

Ingen egne hjelpere eller YAML-automasjoner trengs. Varmtvann og gulvvarme vises bare som planlagte funksjoner.

## Boligen og lading

**Boligen** har felles forbruksgrense, samlet status og målegrunnlag. Med to ladere ligger også **Lademåte** her. **Lading** samler begge laderne med hver sine innstillinger og målinger.

| Betjening | Funksjon |
| --- | --- |
| Automatisk laststyring | Lar SLM regulere laderen. Nye ladere starter avslått. Fra beta 20 beholdes valget ved omstart og oppdatering. Når du slår den av, velges laveste tillatte manuelle strøm; pause, starttid og gyldige målinger respekteres. |
| Automatisk laststyring – lading | Slår automatikk av/på for alle laderne samlet. Hver lader kan fortsatt styres individuelt; andre fremtidige lasttyper påvirkes ikke. |
| Ladepause | Sender 0 A. Ved gjenopptak beregnes ny strøm automatisk, eller tidligere manuell grense gjenopprettes når målinger og grenser tillater det. |
| Manuell ladestrøm | Tilgjengelig når automatikk og ladepause er av. Laderens faktiske minimum og Easees rapporterte maksimum gjelder. Null og lavere verdier kan ikke velges; bruk Ladepause. |
| Fasevalg | Endrer Easees faseinnstilling. SLM bytter ikke automatisk mellom én og tre faser. |
| Tidsstyring og starttid | Eget daglig 12-timers ladevindu per lader. Åpent vindu gir bare tillatelse til lading. |
| Førsteprioritet | Vises med to ladere. Bryterne er koblet sammen, slik at nøyaktig én har førsteprioritet. Dette endrer ikke Easees tekniske master/slave-oppsett. |

**Lad begge** fordeler ledig effekt likt innenfor hver laders strømgrenser. Når bare én får plass, prioriteres den valgte laderen. **Én om gangen** gir den prioriterte, tilgjengelige laderen tur først. Frakobling, pause, avsluttet lading og stengt tidsvindu kan gi den andre laderen tur.

Minste strøm er 11 A ved målt 230 V trefaselading, ellers 6 A. SLM henter øvre strømgrense fra Easee; den skal ikke tastes inn i SLM. Bilen identifiseres ikke, og «Completed» bekrefter ikke batteriprosent.

## Tilkobling og fasevalg

Bekreft faktisk tilkobling per lader: **230 V IT/TT – énfase**, **230 V IT/TT – trefase**, **400/230 V TN – énfase** eller **400/230 V TN – trefase**. Dette er installasjonens tilkobling, ikke ønsket lademodus. Beregningen bruker relevante målte Easee-spenninger, også ved for eksempel 210 V, og setter ikke spenningen fast til 230/400 V. Ved IT/TT brukes den høyeste relevante målte spenningen når flere fasepar inngår, slik at strømgrensen ikke beregnes for høyt.

Ved trefasetilkobling kan fasevalget brukes til énfase, automatisk eller trefaselading. Ved énfasetilkobling vises ikke fasevalget, og direkte forsøk på fasebytte avvises. Manglende nødvendige målinger eller motstridende Easee-opplysninger stanser positiv strømregulering.

Eksisterende ladere må bekreftes under **Konfigurer → Ladere → Ladernes tilkobling**. Endring beholder innstillinger og identiteter, sender 0 A til den lastede laderen og laster SLM på nytt med automatisk styring av. Kvitteringen er ikke en målt bekreftelse på fysisk stopp. Generer YAML-kortet på nytt etter endringen; generatoren utelater fasevalg for énfasetilkoblinger.

## Målinger og navn

Seks hovedsensorer per lader: **Ladestatus**, **Effekt til bilen**, **Strøm til bilen**, **Anbefalt ladestrøm**, **Faser i bruk** og **Volt**. Funksjonen kommer først og ladernavnet sist, også for første lader. Volt viser spenning basert på de relevante terminalmålingene: fase–nøytral ved enfase TN, utledet linjespenning ved trefase TN, og målt fase–fase ved IT/TT. Ladestatus viser bekreftet tilkobling og øvrige elektriske detaljer. TN-forsyningen forblir registrert som 400/230 V selv om bilen lader på én fase.

**Anbefalt ladestrøm** har minimum og Easees maksimum som attributter. **Status for laststyring** på boligen forklarer hvorfor hver lader lader eller venter, med eventuelle faseråd. **Målegrunnlag** viser målekilder, HAN-alder og målingenes gyldighet. Ladeprioritet er en diagnostikksensor ved to ladere.

## Dashboard

Hver lader har overskriften **navn – status**, for eksempel **Garasje – Lader** eller **Tesla – Pauset**, med egen forklaring under. Navnet du har gitt SLM-enheten brukes foran et generisk Easee-navn. «Lader» følger Easees status; anbefalt strøm alene bekrefter ikke at bilen lader. Generer YAML-kortet på nytt for denne overskriften.

Ladetid og brukerbetjening vurderes straks: åpning/lukking av ladevindu, endret starttid, tidsstyring og automatikk av/på, ladepause/gjenopptakelse, fasevalg og førsteprioritet/lademåte. Tidsvinduet åpner ved starttid og stenger nøyaktig 12 timer senere. Start krever fortsatt tillatelse, gyldige målinger og tilstrekkelig kapasitet. Ved to ladere kan målt reduksjon måtte bekreftes først. Vanlig lastregulering følger femminuttersintervallet etter fullført betjening.

Easee-statusen **completed**, bekreftet med 0 W og mindre enn 1 A hvilestrøm, tar den automatiske ladeøkten ut av kapasitetsfordelingen. SLM sender ingen ordinære budsjettkommandoer til den fullførte laderen; siste fysiske strømgrense står urørt. En ny klar-/ventestatus vurderes straks med gyldige målinger, tilgjengelig kapasitet og minste tillatte ladestrøm. Faktisk lading gir vanlig fordeling igjen. Pause, tidsstyring, reelle målefeil og fysiske strømgrenser gjelder fortsatt. Ved aktiv overføring mellom ladere kreves målt reduksjon før økning. Bilen kan begynne å trekke på sist satte grense før Easee rapporterer oppstart; SLM korrigerer ved mottatt signal. Den valgte timemarginen gir energimargin, ingen garantert reaksjonstid. Dette er ikke en måling av batteriprosent.

Måleverdier og ladestatus følger endringer fra kildesensorene i HA. Easee kan melde ladestart før strømmålingen stiger fra 0 A; dette alene stanser ikke lading når bekreftet tilkobling og målte spenninger er gyldige. Ledig kapasitet og anbefalt ladestrøm beregnes ved kildeendringer, i tillegg til en tids- og gyldighetskontroll hvert 30. sekund. Når Easee melder at en nylig tilkoblet bil er klar til lading, vurderer SLM lading straks. Automatisk styring må være på, ladeplanen må tillate lading, pause må være av og nødvendige målinger og kapasitet må være tilgjengelige. Ved to ladere bekreftes nødvendige reduksjoner før kapasitet flyttes. Neste ordinære regulering settes fem minutter etter fullført startregulering. Ladegrensene reguleres ellers normalt hvert femte minutt; uendret grense sendes ikke på nytt. En prognose basert på brukt energi, målereffekt og sist satte ladegrenser avgjør om budsjettet kan holde til neste regulering eller timeskifte. Vedvarende risiko i 30 sekunder kan gi tidligere reduksjon; kan budsjettet ikke vente, reduseres det straks. Pause, ugyldige nødvendige målinger og lavere fysisk strømgrense håndteres straks. Etter en tidlig reduksjon venter ordinær økning minst fem minutter. Kortet skiller mellom anbefalt strøm nå, sist satt grense og målt strøm. Markdown-kortet viser målereffekt (W), brukt energi denne timen (kWh) og forventet timeforbruk (kWh) på en kompakt linje. Manglende verdier vises som —. Generer kortet på nytt for å få dette oppsettet.

Kjør `smart_load_manager.get_dashboard` under **Settings → Tools → Actions**. Kopier `yaml` til et **Manuelt kort i en eksisterende seksjon**. Generatoren bruker de faktiske entitets-ID-ene, også når du har gitt dem egne navn. Grafen leser EnergyTariff direkte.

De statiske [ett-lader](../examples/lovelace/charging_card.yaml)- og [to-lader](../examples/lovelace/two_chargers_card.yaml)-kortene er maler. Generer helst kortet for din installasjon.

## Konfigurasjon

**Konfigurer → Boligens målekilder og sikkerhetsmargin** validerer alt før lagring og påvirker ikke ladeinnstillingene. Nye kilder leses ved neste ordinære oppdatering.

**Konfigurer → Ladere → Legg til lader** viser bare ledige Easee-enheter og beholder den eksisterende laderen. **Fjern lader** er et eget valg når to ladere er konfigurert. Integrasjonen lastes på nytt; eksisterende laderes lagrede på/av-valg beholdes. En lader som fjernes, får en 0 A-kommando før oppsettet endres; feil ved denne kommandoen avbryter endringen. Dette er ikke en målt bekreftelse på at fysisk lading har stoppet. Innstillinger beholdes ved senere gjeninnlegging.

## Hvis lading venter

Les først boligens status og Målegrunnlag. Kontroller HAN, EnergyTariff, aktiv Easee-spenningssensor, rapportert strømgrense, pause og tidsvindu. HAN må være gyldig og høyst 120 sekunder gammel. En uendret, tilgjengelig Easee-effektverdi er gyldig selv med gammelt tidsstempel. Fordeling venter på nye målinger som bekrefter en reduksjon før mer strøm gis til den andre laderen.

SLM erstatter ikke vern eller installasjonens elektriske begrensninger. Automatikk av betyr at SLM slutter å regulere; Easee beholder siste dynamiske grense. Bruk Ladepause for en uttrykkelig 0 A-kommando.

## Valg av ladere

Hele oppsettet skjer i Home Assistants vanlige dialog, også i Companion-appen. Velg **Elbillading – Easee**, velg første lader i enhetsvelgeren med integrasjonslogo, og fullfør med én eller legg til en til.

Når du legger til en lader, står den første allerede som valgt. Behold den og bruk det tomme feltet under til å velge én ny lader. Home Assistant utelater de valgte enhetene fra dette legg-til-feltet. Bekreft deretter valgene i samme dialog. Bruk **Fjern lader** for å fjerne en konfigurert lader; tillegging erstatter aldri eksisterende oppsett.

Ved senere tillegging brukes **Legg til lader** under Konfigurer → Ladere. Eksisterende lader og innstillinger beholdes. Avbryter du førstegangsoppsettet før fullføring, opprettes ingen delvis installasjon.

### Når må dashboardkortet genereres på nytt?

Kjør `smart_load_manager.get_dashboard` og erstatt YAML-en i det eksisterende manuelle kortet når du legger til, fjerner eller bytter lader, endrer HAN-kilde eller entitets-ID-er som kortet bruker, endrer ladernavn som står i kortoverskriftene, eller tar i bruk en funksjon med endret kortoppsett. Kortets YAML oppdateres ikke automatisk. Vanlige endringer i forbruksgrense, sikkerhetsmargin, prioritet, lademåte, tidsplan, fasevalg og pause krever ikke nytt kort; verdiene oppdateres i visningen. Ta vare på egne manuelle korttilpasninger før du erstatter YAML-en.

Kortet bruker en kort overskrift og tre kompakte kolonner: målereffekt i kW, brukt energi og estimat. Verdiene avrundes bare i visningen; beregningene beholder presisjonen. Ved svært høye energiverdier vises MWh. Når ingen bil er tilkoblet, skjules de gjentatte laderavsnittene. Ved blandet tilkobling vises hvilken lader som har bil og hvilken som er frakoblet. Effekt, anbefalt/sist satt ampere og neste regulering vises bare når Easee melder lading. Ventende, pauset og fullført beholder forklaringen. Generer YAML-kortet på nytt for dette oppsettet.


## Statuskortet i beta 16

Kortet viser boligens målinger og grense øverst, deretter lasttype og navnet på hver last. Hver last har én status og Auto/Manuell. En kort årsak eller handling vises bare når den er relevant. Skillelinjer deler lasttypene; bare kategorier som er satt opp vises. Effekt, strømgrense og neste regulering vises under aktiv lading. Varmekabler og varmtvann i forhåndsskissene er planlagt funksjonalitet. Hent nytt YAML-kort med `smart_load_manager.get_dashboard` etter den kommende oppdateringen.


En uendret HAN-verdi er fortsatt fersk når måleren rapporterer den på nytt. Hvis rapportene stopper, stanser automatisk regulering etter den gjeldende aldersgrensen. Kortet beholder en lesbar tallverdi med varsel om at målingen ikke er oppdatert; verdien brukes ikke som ferskt reguleringsgrunnlag. Ukjent/utilgjengelig kilde vises uten tall. Status fra Easee beholdes uendret.


## Feilsøkingsfil i beta 16

Åpne **Innstillinger → Enheter og tjenester → Smart Load Manager OJM → integrasjonsoppføringen → ⋮ → Last ned diagnostikk**. Last ned filen mens feilen er aktuell, før omstart eller omlasting, og legg den ved feilrapporten med tidspunktet du observerte problemet. Filen viser anonyme laster, målegrunnlag, reguleringsvalg og forsøk/resultat for strøm- og fasekommandoer. Den lagrer de siste 4096 hendelsene i minnet og oppgir antall overskrevne hendelser. Ingen fast tidsperiode er garantert. Historikken nullstilles ved omstart/omlasting og kan ikke hente eldre hendelser. Et vellykket tjenestekall bekrefter ikke fysisk lading. Innloggingsdata, navn og kilde-ID-er utelates. Funksjonen er tilgjengelig fra beta 16.


I beta 16 godtas gyldige HAN-rapporter opptil **120 sekunder** gamle, inkludert nøyaktig 120 sekunder. Beta 15 brukte 60 sekunder. Ferskhet måles fra siste rapportering, også når verdien er uendret. Eldre eller ugyldige målinger holder automatisk lading igjen ved neste kontroll.


Ved åpning av tidsvindu, gjenopptak etter ladepause eller aktivering av automatikk skal en avsluttet økt vurderes på nytt med gjeldende kapasitet. Dette korrigeres i neste beta etter at beta 16 viste en fastlåst nullgrense. Aktiv tidsstyring gjelder fortsatt også ved manuell ladestrøm; slå av tidsstyring hvis du vil lade utenfor vinduet.


Ved manglende HAN-rapportering sendes 0 A én gang per berørt styrt lader når kommandoen lykkes. Nye målinger gir straks en ny vurdering av tillatt strøm; vanlig femminuttersventing gjelder ikke denne gjenopprettingen. Pause, tidsstyring, kapasitet og bekreftet reduksjon på den andre laderen gjelder fortsatt. Mislykkede stopp kan forsøkes på nytt.






Beta 17: Oppdater integrasjonen og start Home Assistant på nytt. Kort fra beta 16 kan beholdes; beta 17 endrer ikke kortoppsettet. Test ny lading etter økt ladegrense i bilappen og last ned diagnostikk straks ved avvik.

Beta 19: Oppdater og start HA på nytt. Eksisterende dashboard-YAML kan beholdes. Diagnostikken viser completed_capacity_released og completed_control_resumed; Målegrunnlag har attributtet completed_capacity_released. Fysisk fullføring, ny ladeforespørsel og to-lader-test gjenstår.


Beta 20 (klargjort): SLM lagrer automatikk per lader, ladepause, tidsstyring, starttid, manuell strøm og boligens budsjett/fordelingsvalg. Disse beholdes ved vanlig omstart, omlasting og oppdatering. Fasevalget lagres hos Easee og leses tilbake derfra. Nye ladere starter fortsatt med automatikk av. Beta 19 lagret ikke automatikkvalget: etter første oppdatering til beta 20 må automatikk derfor aktiveres én gang. Bekreftet endring av fysisk tilkobling eller fjerning av en lader slår fortsatt av den berørte laderen. Oppstart vurderer alltid målinger, pause, tidsstyring og strømgrenser før lading tillates. Eksisterende YAML kan beholdes.
