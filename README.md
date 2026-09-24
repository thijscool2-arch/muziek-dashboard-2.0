# Muziekdashboard

Upload de volledige inhoud van deze map naar de hoofdmap van je GitHub-repository.
Alle Python-, CSV-, JSON- en Markdown-bestanden staan naast elkaar. Er is geen map data nodig:
in app.py staat map_data = map_dashboard.

## Starten

Lokaal vanuit deze map:

    python -m streamlit run app.py

Streamlit Cloud: repository muziek-dashboard, branch main, startbestand app.py,
Python 3.13. requirements.txt installeert de benodigde pakketten.

## Wat staat in de app?

1. Muziekvoorkeuren: dagelijks versus studeren bij dezelfde 98 studenten.
   De checkbox wisselt tussen beide gemiddelden en het verschil. Het grootste
   verschil is geannoteerd; ook patronen en positie onderscheiden de groepen.
2. Muziek en ervaringen: uitkomst en studiecontext filteren meerdere grafieken.
   Contextkeuzes hangen af van de beschikbare antwoorden voor de uitkomst.
   Een aparte uitsplitsing onderzoekt studiecontext als mogelijke andere verklaring.
3. Data en bronnen: ontbrekende waarden, bereiken, dubbele rijen, opschoonkeuzes
   en de aantallen vóór en na de koppeling. De conclusie vat de gevonden resultaten samen.

De originele dataframebestanden blijven intact. Alleen de grafiektabellen worden gefilterd.
De trendlijnen blijven verkennend. Er zijn geen nieuwe pakketten nodig.

## Ontbrekende genres aanvullen

`muziek_api.py` zoekt titel en artiest op via de openbare iTunes Search API.
Er is geen token nodig. `itunes_cache.json` bevat de opgehaalde resultaten;
upload ook deze twee bestanden naast app.py. Zo start het dashboard meteen.

In tabblad 2 kun je de aangevulde genres aan- en uitzetten. De labels vermelden
de bron omdat Spotify en iTunes verschillende genre-indelingen hebben.
In tabblad 3 staan aantallen vóór/na, bronlinks en de knop om opnieuw op te halen.
Dit duurt ongeveer 8 minuten door de API-limiet. Bij een storing blijven eerdere
resultaten beschikbaar. Vernieuwde resultaten blijven in de huidige dashboardsessie;
download daarna itunes_cache.json en vervang die in GitHub om ze blijvend te bewaren.
De eindtabel met de aangevulde kolommen kun je daar ook downloaden.

Lokaal alle nog niet opgezochte nummers ophalen en de cache opslaan:

    python muziek_api.py

## Audiokenmerken aanvullen

`audio_api.py` gebruikt de openbare ReccoBeats-API, eveneens zonder token.
Upload ook dit bestand en `reccobeats_cache.json` naast app.py. De app vult
ontbrekende energy, valence, tempo en danceability direct aan in de bestaande kolommen,
met bronvermelding. Bestaande waarden blijven behouden. In de audiografiek
kies je ReccoBeats of de oorspronkelijke Spotify-dataset: bronnen worden
niet in één trendlijn gemengd. Alle oorspronkelijke grafieken blijven beschikbaar.

Opnieuw ophalen kan in tabblad 3; download de vernieuwde reccobeats_cache.json
als je die blijvend wilt bewaren. Of haal lokaal nog ontbrekende nummers op met:

    python audio_api.py

Er worden alleen songtitels/artiesten naar Apple en Spotify-track-ID's naar
ReccoBeats gestuurd, geen student-ID's of scores. Ontbrekende studentmetingen
worden niet geschat of ingevuld. Er zijn nog steeds geen extra pakketten nodig.
Bronvermelding en de nog aan te vullen oorspronkelijke datasetlinks staan in BRONNEN.md.

## Eind-df

`dashboard_aangevuld.csv` bevat de complete df met de gevonden waarden direct
in track_genre, energy, valence, tempo en danceability. Alleen lege waarden
zijn ingevuld. Alle rijen blijven behouden. Twee bronkolommen vermelden de herkomst.
De oorspronkelijke CSV-bestanden blijven bewaard. De app bouwt df opnieuw op
uit die bestanden en de API-cache; na verversen download je de nieuwste eindtabel
in tabblad 3. De CSV is een opgeslagen momentopname voor gebruik in het notebook.
