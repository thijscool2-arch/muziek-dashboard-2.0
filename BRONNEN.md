Code opgesteld met hulp van Codex en aangepast aan de eigen kolommen en datasets.
De officiële documentatie is gebruikt om de grafieken en bediening te controleren:

- [Plotly: individuele punten per categorie](https://plotly.com/python/strip-charts/)
- [Plotly: foutbalken](https://plotly.com/python/error-bars/)
- [Streamlit: slider](https://docs.streamlit.io/develop/api-reference/widgets/st.slider)
- [Streamlit: checkbox](https://docs.streamlit.io/develop/api-reference/widgets/st.checkbox)
- [Streamlit: dropdown](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox)

De data komen uit de aangeleverde bestanden `dataset 1 case 2.zip` en
`dataset 3 case 2.xlsx`. Voeg voor de inlevering ook hun oorspronkelijke
publicatielinks/auteurs toe; die zijn niet uit de lokale bestandsnamen vast te stellen.

Kunnen uitleggen: de slider filtert genres op het aantal geldige antwoorden;
de dropdown wisselt de uitkomstmaat; de checkbox toont/verbergt de samenvatting.
Foutbalken tonen standaarddeviatie, geen betrouwbaarheidsinterval. Deelnemers
kunnen meerdere antwoorden hebben gegeven. Vergelijkingen zijn beschrijvend.

- [Plotly: lineaire trendlijnen](https://plotly.com/python/linear-fits/)
De trendlijn in grafiek 5 is een verkennende lineaire fit; bij weinig antwoorden is de lijn onzeker.

De extra grafieken gebruiken dataset 1 case 2.zip voor Spotify-kenmerken en
dataset 2 case 2.xlsx voor de muziekvoorkeuren van 98 studenten. Genrenamen van
de vragenlijst zijn uit index.xlsx gehaald. De twee contexten zijn herhaalde
beoordelingen door dezelfde mensen, geen 196 verschillende studenten.
Deze figuren gebruiken geen merge en doen geen uitspraak over een effect van
muziek op energie of stemming. Originele publicatielinks van de datasets moeten
nog worden aangevuld zodra ze beschikbaar zijn.

## Aanpassingen voor de rubric

- [Streamlit: tabbladen](https://docs.streamlit.io/develop/api-reference/layout/st.tabs)
- [Plotly: patronen naast kleur](https://plotly.com/python/pattern-hatching-texture/)

De voorkeursvergelijking berekent per genre: gemiddeld tijdens studeren minus gemiddeld dagelijks.
In de aangeleverde vragenlijst zijn beide metingen voor alle 98 studenten aanwezig.
Het grootste absolute verschil wordt gemarkeerd; dit is geen statistische significantietoets.

De contextvergelijking groepeert oorspronkelijke antwoorden op wel/niet studeren,
toont aantal en gemiddelde en vergelijkt die beschrijvend. De groepen zijn niet
gerandomiseerd en dezelfde deelnemer kan meerdere antwoorden geven. Daarom is
dit een onderzoek van een mogelijke andere verklaring, geen causaal effect.

## Aanvulling via de openbare iTunes Search API

- [Apple: verzoeken, velden en limieten](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html)
- [Spotify: beperking toegang tot audiokenmerken voor nieuwe apps](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api)

`muziek_api.py` vraagt https://itunes.apple.com/search op met `term=titel artiest`,
`entity=song`, `country=NL` en `limit=50`. Er is geen API-token nodig. De responsvelden
trackName, artistName en primaryGenreName worden gebruikt voor de koppeling;
trackId en trackViewUrl leggen de herkomst vast. Zoek-URL en UTC-ophaaltijd staan
in itunes_cache.json. Er wordt alleen gezocht voor ontbrekende Spotify-genres.

De sleutel is titel + artiest, genormaliseerd voor hoofdletters, accenten,
leestekens en herstelbare tekencodering. Versiewoorden zoals live en remix blijven
deel van de sleutel. Beide velden moeten overeenkomen. Bij meerdere gevonden
genres of zonder exacte match vullen we niets in. Resultaten buiten de eerste
50 zoekresultaten worden niet onderzocht; niet gevonden betekent dus niet dat
een nummer niet bestaat. Dit is conservatieve automatische matching, geen
handmatige verificatie van iedere opname.

Er zit minstens 3,2 seconden tussen verzoeken (Apple noemt circa 20 per minuut).
Netwerkfouten en tijdelijke HTTP-fouten worden maximaal tweemaal opnieuw geprobeerd.
Bij een storing blijven eerdere resultaten staan. De opgeslagen cache maakt
de eerste pagina onafhankelijk van een werkende API. De app kan via een knop
zelf nieuwe API-verzoeken uitvoeren. De cache is ook opnieuw op te bouwen met
`python muziek_api.py` en bevat geen deelnemer-ID's of studentenmetingen.

Het oorspronkelijke bronbestand blijft gelijk. In de eind-df blijven bekende
Spotify-genres staan en vult iTunes alleen lege plekken in track_genre.
Genrebron vermeldt Spotify of iTunes. De koppeling is een lookup, zodat er geen
rijen bijkomen of verdwijnen. Het dashboard vermeldt de aantallen voor en na
op basis van oorspronkelijke antwoorden. De grafiek houdt de bronindelingen
apart; bijvoorbeeld Spotify-pop en iTunes-Pop worden niet één categorie.
Energy, valence, tempo, danceability, popularity en studentmetingen worden
niet door iTunes geleverd of ingevuld. De kwaliteitscontrole toont zowel
de oorspronkelijke kolommen als de aangevulde kolommen.

## Audiokenmerken uit ReccoBeats

- [ReccoBeats: API zonder authenticatie](https://reccobeats.com/docs/documentation/introduction)
- [ReccoBeats: meerdere audiokenmerken ophalen](https://reccobeats.com/docs/apis/get-audio-features)
- [ReccoBeats: limieten en retries](https://reccobeats.com/docs/documentation/rate-limiting)

`audio_api.py` gebruikt GET https://api.reccobeats.com/v1/audio-features?ids=...
in batches van 20 unieke Spotify-track-ID's. De oorspronkelijke track_id krijgt
voorrang; ontbreekt die, dan gebruiken we de ingevulde Spotify ID na verwijderen
van het URI-/URL-prefix. Alleen geldige track-ID's worden verstuurd.

De teruggestuurde href bevat de Spotify-ID; die koppelt iedere respons aan de
goede rij, ongeacht de volgorde van resultaten. Velden: energy, valence, tempo,
danceability, id en href. Waarden buiten 0–1 bij de eerste, tweede en vierde
variabele en negatieve tempo's worden niet overgenomen. Tijdstip, API-URL,
ReccoBeats-ID, status en kenmerken staan in reccobeats_cache.json. Bestaande
gegevens krijgen voorrang. Alleen lege plekken in energy, valence, tempo en
danceability worden ingevuld; 'Aanvulling audiobron' vermeldt ReccoBeats. Bij een
audiomatch wordt ook het exacte Spotify-track-ID ingevuld. Geen rijen toegevoegd
of verwijderd. dashboard_aangevuld.csv bevat de eind-df als momentopname.

De meetmethoden zijn niet als identiek aan Spotify gevalideerd. Daarom kun je
in de audiografiek één bron kiezen en worden geen gezamenlijke trendlijnen
over gemengde bronnen berekend. De gecombineerde download is geschikt om
dekking te bekijken, maar bronverschillen moeten bij verdere analyses worden
meegenomen. Popularity blijft ongewijzigd: huidige populariteit is niet
zonder meer gelijk aan de populariteit ten tijde van de vragenlijst.

De API heeft één seconde pauze tussen batches, maximaal twee retries bij
tijdelijke fouten en respecteert numerieke Retry-After-headers. De app laadt
de cache zonder netwerkverzoek en kan via een knop zelf de API ophalen.
Bij netwerkfouten blijft een eerdere respons beschikbaar. De studentmetingen
blijven ongewijzigd; we schatten of verzinnen geen ontbrekende antwoorden.

### Resultaat van ophalen op 24 september 2026

De oorspronkelijke 280 antwoorden en 323 mergerijen zijn behouden. iTunes:
126 unieke titel-artiestcombinaties onderzocht, 62 met een eenduidig genre;
dat vult genres aan bij 76 antwoorden (201 ontbrekend wordt 125).
ReccoBeats: 158 unieke track-ID's onderzocht, 126 met audiokenmerken;
dat vult vier audiokenmerken aan bij 93 antwoorden (elk van 201 ontbrekend naar 108).
De energieverschil-per-genre-grafiek heeft nu 42 bruikbare antwoorden in plaats
van 18. De audiografiek met energieverschil heeft 48 antwoorden bij keuze
ReccoBeats, tegenover 18 bij de oorspronkelijke Spotify-bron. Dit zijn
antwoorden, geen unieke studenten. Herhaald API-ophalen kan andere resultaten geven.
