from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st
from muziek_api import haal_genres_op, lees_cache, vul_genres_aan
from audio_api import KENMERKEN, audio_voor_grafiek, haal_audio_op, vul_audio_aan

from grafieken import (
    METINGEN, audio_data, dekking, plot_audio, plot_genre,
    plot_taak, plot_verdeling, samenvatting, selectie, voorbereiden,
)

st.set_page_config(page_title="Muziek en studeren", layout="wide")
st.title("Muziek en studeren")
st.write("**Onderzoeksvraag:** welke muziek verkiezen studenten tijdens het studeren, "
         "en welke samenhang zien we met energie, stemming en studiemoeilijkheid?")

# Alle uploadbestanden staan naast app.py, zoals in de GitHub-repository.
map_dashboard = Path(__file__).resolve().parent
map_data = map_dashboard
try:
    df = pd.read_csv(map_data / "dashboard_data.csv")
    herkomst = pd.read_csv(map_data / "grafiekdata.csv")
    controle = ["track_id", "track_genre", "Studietaak", *METINGEN,
                "energy", "valence", "tempo", "danceability"]
    pd.testing.assert_frame_equal(df[controle], herkomst[controle], check_dtype=False)
    origineel = df.copy()
    originele_data = voorbereiden(origineel, herkomst)
    cache = st.session_state.get("itunes_cache", lees_cache(map_data / "itunes_cache.json"))
    df = vul_genres_aan(df, cache)
    audio_cache = st.session_state.get("reccobeats_cache", lees_cache(map_data / "reccobeats_cache.json"))
    df = vul_audio_aan(df, audio_cache)
    data = voorbereiden(df, herkomst)
    voorkeuren = pd.read_csv(map_data / "studenten_voorkeuren.csv")
    spotify = pd.read_csv(map_data / "spotify_genres.csv")
    broninfo = json.loads((map_data / "broninfo.json").read_text(encoding="utf-8"))
except FileNotFoundError as fout:
    st.error(f"Bestand ontbreekt: {Path(fout.filename).name}. Upload dit naast app.py.")
    st.stop()
except (ValueError, KeyError, AssertionError):
    st.error("De databestanden passen niet bij elkaar. Upload alle CSV-bestanden uit dezelfde lokale dashboardmap.")
    st.stop()

# Alleen voor de analyses: ieder oorspronkelijk antwoord eenmaal. df blijft intact.
antwoorden = data.drop_duplicates("_bronrij").copy()
originele_antwoorden = originele_data.drop_duplicates("_bronrij")
st.caption(f"We beginnen met voorkeuren van {broninfo['studenten']} studenten. "
           f"Daarna bekijken we {len(antwoorden)} antwoorden uit een aparte meting "
           "en muziekkenmerken uit Spotify. Dit zijn verschillende datasets en geen bewezen oorzakelijke effecten.")
tab1, tab2, tab3 = st.tabs(["1. Muziekvoorkeuren", "2. Muziek en ervaringen", "3. Data en bronnen"])

with tab1:
    st.subheader("Veranderen voorkeuren tijdens het studeren?")
    st.write("Dezelfde studenten beoordeelden genres voor dagelijks luisteren en voor studeren. "
             "Zo kunnen we de twee situaties direct vergelijken zonder een Spotify-match nodig te hebben.")
    vergelijking = voorkeuren.pivot(index="Genre", columns="Context", values="Gemiddelde")
    vergelijking["Verschil"] = vergelijking["Tijdens studeren"] - vergelijking["Dagelijks"]
    vergelijking["Aantal"] = voorkeuren.groupby("Genre")["Aantal"].min()
    vergelijking = vergelijking.sort_values("Verschil")
    grootste = vergelijking["Verschil"].abs().idxmax()
    verschil = vergelijking.loc[grootste, "Verschil"]
    toon_verschil = st.checkbox("Toon het verschil in plaats van de twee gemiddelden", value=True)
    if toon_verschil:
        fig = px.bar(vergelijking.reset_index(), x="Verschil", y="Genre", orientation="h",
                     text=vergelijking["Verschil"].map(lambda x: f"{x:+.2f}"),
                     hover_data=["Aantal"],
                     labels={"Verschil": "Studievoorkeur minus dagelijkse voorkeur"})
        fig.add_vline(x=0, line_color="gray", line_dash="dash")
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.add_annotation(x=verschil, y=grootste, text="Grootste verschil",
                           showarrow=True, ax=100, ay=-30)
    else:
        fig = px.bar(voorkeuren, x="Gemiddelde", y="Genre", color="Context",
                     pattern_shape="Context", orientation="h", barmode="group",
                     category_orders={"Genre": vergelijking.index.tolist()},
                     hover_data=["Aantal"], labels={"Gemiddelde": "Gemiddelde voorkeursscore"},
                     color_discrete_map={"Dagelijks": "#0072B2", "Tijdens studeren": "#D55E00"},
                     pattern_shape_map={"Dagelijks": "", "Tijdens studeren": "/"})
        fig.update_layout(legend=dict(orientation="h", y=1.07))
    fig.update_layout(height=850, margin=dict(l=10, r=80, t=60, b=40))
    st.plotly_chart(fig, use_container_width=True, key="voorkeuren")
    st.caption(f"{broninfo['studenten']} studenten, {broninfo['student_genres']} genres; "
               "beweeg over een balk voor het aantal geldige antwoorden. "
               "De twee situaties zijn geen twee onafhankelijke groepen.")
    st.write(f"**Wat zien we?** {grootste} heeft het grootste verschil: {verschil:+.2f} punten "
             "(studeren min dagelijks). Dit beschrijft voorkeur, niet een effect op concentratie.")

    st.subheader("Welke muziekkenmerken hebben Spotify-genres?")
    st.write("Deze bron geeft context bij de muziek zelf. De genre-indeling verschilt van de vragenlijst; "
             "we koppelen deze genre-gemiddelden niet automatisch aan studenten.")
    kenmerk = st.selectbox("Vergelijk muziekkenmerk", ["energy", "valence", "tempo", "danceability"])
    st.caption("energy = intensiteit van het geluid; valence = positieve klank; "
               "tempo = beats per minuut; danceability = dansbaarheid. "
               "Spotify-energy is dus niet de ervaren energie van een student.")
    aantal = st.slider("Aantal genres met het hoogste gemiddelde", 5, int(broninfo["spotify_genres"]), 15)
    sub = spotify[spotify["Kenmerk"] == kenmerk].nlargest(aantal, "Gemiddelde").sort_values("Gemiddelde")
    fig = px.bar(sub, x="Gemiddelde", y="Genre", orientation="h", hover_data=["Aantal"],
                 labels={"Gemiddelde": f"Gemiddelde {kenmerk}", "Aantal": "Geldige Spotify-rijen"})
    fig.update_layout(height=max(450, 25 * aantal + 100))
    st.plotly_chart(fig, use_container_width=True, key="spotify")
    st.caption(f"{broninfo['spotify_gebruikt']:,} bruikbare Spotify-rijen; dubbele bronrijen blijven behouden. "
               "Dit is een ranglijst van de gekozen hoogste gemiddelden, geen volledig overzicht.")

with tab2:
    st.subheader("Hangen muziek en ervaringen samen?")
    st.write("Deze kleinere dataset bevat begin- en eindmetingen. Ontbreekt een van beide, "
             "dan berekenen we geen verschil. Een positieve verschilscore betekent een hogere latere meting.")
    meting = st.selectbox("Kies uitkomst", METINGEN)
    beschikbare_contexten = antwoorden.loc[antwoorden[meting].notna(), "Aan het studeren"].dropna().unique()
    contexten = {"Alle antwoorden": None, **{
        ("Tijdens studeren" if waarde == "Yes" else "Niet tijdens studeren"): waarde
        for waarde in ("Yes", "No") if waarde in beschikbare_contexten
    }}
    context = st.selectbox("Studiecontext bij deze uitkomst", list(contexten))
    gekozen = data if contexten[context] is None else data[data["Aan het studeren"] == contexten[context]]
    st.caption("De uitkomst en studiecontext werken door in alle grafieken in dit tabblad. "
               "De beschikbare contexten hangen af van de gekozen uitkomst.")
    gebruik_api = st.checkbox("Gebruik ook aangevulde genres uit iTunes", value=True)
    genre_data = gekozen.copy()
    if gebruik_api:
        genre_data["track_genre"] = gekozen["track_genre"] + " [" + gekozen["Genrebron"] + "]"
    else:
        genre_data["track_genre"] = origineel.loc[gekozen.index, "track_genre"]
    st.caption("iTunes vult alleen ontbrekende genres aan. De bron staat bij het genre: "
               "Spotify en iTunes gebruiken verschillende indelingen, dus hun genrenamen worden niet samengevoegd.")
    minimum = st.slider("Minimumaantal geldige antwoorden per genre", 1, 20, 1)
    toon_tabel = st.checkbox("Toon de tabel bij de genrevergelijking", value=True)
    sub = selectie(genre_data, "track_genre", meting, minimum)
    st.caption(dekking(gekozen, sub))
    st.plotly_chart(plot_genre(genre_data, meting, minimum), use_container_width=True, key="genre")
    if toon_tabel:
        st.dataframe(samenvatting(genre_data, "track_genre", meting, minimum), hide_index=True)
    st.write("Elk punt telt één oorspronkelijk antwoord per genre. "
             "Een deelnemer kan meerdere antwoorden geven en een nummer kan bij meerdere genres horen. "
             "Verschillen tussen genres met weinig antwoorden zijn daarom onzeker.")

    st.subheader("Andere verklaring: de studiecontext")
    st.write("Misschien hangt een verschil ook samen met wel of niet studeren. "
             "Hier vergelijken we beide contexten voor de gekozen uitkomst, vóór het contextfilter.")
    context_tabel = (antwoorden.groupby("Aan het studeren")[meting]
                     .agg(Antwoorden="count", Gemiddelde="mean").query("Antwoorden > 0")
                     .rename(index={"Yes": "Tijdens studeren", "No": "Niet tijdens studeren"}))
    st.dataframe(context_tabel.round(2))
    if len(context_tabel) == 2:
        contextverschil = (context_tabel.loc["Tijdens studeren", "Gemiddelde"]
                           - context_tabel.loc["Niet tijdens studeren", "Gemiddelde"])
        st.write(f"Het gemiddelde tijdens studeren ligt {contextverschil:+.2f} punten ten opzichte van niet studeren. "
                 "De groepen zijn niet willekeurig samengesteld: dit is een mogelijke andere verklaring, "
                 "geen bewijs dat studeren of muziek het verschil veroorzaakt.")
    else:
        st.info("Voor deze uitkomst heeft slechts één context geldige antwoorden; een vergelijking is niet mogelijk.")

    st.subheader("Vergelijk ook de studietaken")
    st.caption(dekking(gekozen, selectie(gekozen, "Studietaak", meting)))
    st.write("De taak kan ook verschil maken. De balken tonen gemiddelden, de boxplot toont de spreiding. "
             "Het genre-minimumfilter geldt hier niet.")
    st.plotly_chart(plot_taak(gekozen, meting), use_container_width=True, key="taak_gemiddelde")
    st.plotly_chart(plot_taak(gekozen, meting, box=True), use_container_width=True, key="taak_spreiding")

    st.subheader("Audiokenmerken en de gekozen uitkomst")
    audiobron = st.selectbox("Bron van de audiokenmerken", ["ReccoBeats API", "Oorspronkelijke Spotify-dataset"])
    audio_selectie = audio_voor_grafiek(gekozen, audio_cache) if audiobron == "ReccoBeats API" else originele_data.loc[gekozen.index]
    st.caption(dekking(audio_selectie, audio_data(audio_selectie, meting)))
    st.plotly_chart(plot_audio(audio_selectie, meting), use_container_width=True, key="audio")
    st.caption(f"Bron: {audiobron}. We berekenen de trendlijnen per gekozen bron. "
               "Gelijke namen zoals energy betekenen niet dat beide bronnen exact dezelfde meetmethode gebruiken.")
    st.caption("De trendlijn is verkennend. Elk punt is één antwoord; bij meerdere gekoppelde tracks "
               "middelen we hun kenmerken. Weinig antwoorden en herhaalde deelnemers beperken de conclusie.")
    st.subheader("Verdeling van alle beschikbare antwoorden in deze selectie")
    st.caption(dekking(gekozen, selectie(gekozen, None, meting)))
    st.plotly_chart(plot_verdeling(gekozen, meting), use_container_width=True, key="verdeling")

with tab3:
    st.subheader("Ontbrekende genres aangevuld via een openbare API")
    extra = int((antwoorden["Genrebron"] == "iTunes").sum())
    ontbrekend = int(originele_antwoorden["track_genre"].isna().sum())
    st.write(f"Bij {extra} extra oorspronkelijke antwoorden is een genre gevonden. "
             f"Ontbrekende genres: {ontbrekend} vóór aanvullen, {ontbrekend - extra} erna. "
             "Titel én artiest moeten overeenkomen; bij twijfel blijft de waarde leeg.")
    st.write("De genres staan direct in **track_genre**; **Genrebron** vermeldt de bron. "
             "Alleen lege waarden zijn ingevuld; alle rijen blijven behouden. iTunes levert geen Spotify-energy, "
             "valence of danceability; daarvoor bekijken we hieronder ReccoBeats. "
             "Ontbrekende antwoorden van studenten kunnen we met geen van beide invullen.")
    st.caption("Bron: Apple iTunes Search API (Nederlandse catalogus). Geen account of token nodig. "
               "Alleen songtitels en artiestnamen gaan naar Apple. De opgeslagen resultaten laden direct; "
               "opnieuw ophalen duurt ongeveer 8 minuten vanwege de verzoeklimiet.")
    if not cache:
        st.info("Nog geen opgeslagen API-resultaten. Upload itunes_cache.json naast app.py "
                "of haal de genres hieronder op.")
    if st.button("Haal genres opnieuw op via iTunes"):
        balk = st.progress(0, text="Genres ophalen…")

        def voortgang(i, totaal, resultaten):
            balk.progress(i / totaal, text=f"{i} van {totaal} nummers opgezocht")

        bijgewerkt = haal_genres_op(origineel, cache, voortgang=voortgang, ververs=True)
        st.session_state["itunes_cache"] = bijgewerkt
        st.rerun()
    fouten = sum(str(r.get("status", "")).startswith("API") for r in cache.values())
    if fouten:
        st.info(f"Bij {fouten} zoekopdrachten was de API niet bereikbaar. "
                "Beschikbare gegevens blijven bruikbaar; je kunt later opnieuw ophalen.")
    controle_api = pd.DataFrame(cache.values())
    if not controle_api.empty:
        with st.expander("Bekijk de API-resultaten en bronlinks"):
            st.dataframe(controle_api, hide_index=True)
    st.download_button("Download opgeslagen API-resultaten",
                       json.dumps(cache, ensure_ascii=False, indent=2).encode("utf-8"),
                       "itunes_cache.json", "application/json")
    st.subheader("Audiokenmerken aangevuld via ReccoBeats")
    audio_controle = pd.DataFrame({
        "Ontbrekend vóór": originele_antwoorden[KENMERKEN].isna().sum(),
        "Ontbrekend na": antwoorden[KENMERKEN].isna().sum()
    })
    st.dataframe(audio_controle)
    st.caption("Aantal oorspronkelijke antwoorden, niet het aantal mergerijen. "
               "ReccoBeats is gekoppeld op exact Spotify-track-ID. Geen account of token nodig.")
    st.write("Energy, valence, tempo en danceability behouden bekende waarden; ReccoBeats vult alleen lege plekken. "
             "De bron staat in 'Aanvulling audiobron'. Dit zijn gegevens uit een andere muziekbron; "
             "daarom kies je in de audiografiek één bron tegelijk. Popularity en studentenmetingen blijven ongewijzigd.")
    if not audio_cache:
        st.info("Upload reccobeats_cache.json naast app.py of haal de audiokenmerken hieronder op.")
    if st.button("Haal audiokenmerken opnieuw op via ReccoBeats"):
        balk_audio = st.progress(0, text="Audiokenmerken ophalen…")

        def audio_voortgang(i, totaal, resultaten):
            balk_audio.progress(i / totaal, text=f"{i} van {totaal} track-ID's opgezocht")

        st.session_state["reccobeats_cache"] = haal_audio_op(origineel, audio_cache, audio_voortgang, ververs=True)
        st.rerun()
    audio_fouten = sum(r.get("status", "").startswith("API") for r in audio_cache.values())
    if audio_fouten:
        st.info(f"Bij {audio_fouten} track-ID's was de API niet bereikbaar. Je kunt later opnieuw ophalen.")
    with st.expander("Bekijk de ReccoBeats-resultaten en bronlinks"):
        st.dataframe(pd.DataFrame.from_dict(audio_cache, orient="index").rename_axis("Spotify-track-ID"))
    st.download_button("Download opgeslagen audiokenmerken",
                       json.dumps(audio_cache, ensure_ascii=False, indent=2).encode("utf-8"),
                       "reccobeats_cache.json", "application/json")
    st.download_button("Download eindtabel met aangevulde gegevens", df.to_csv(index=False).encode("utf-8-sig"),
                       "dashboard_aangevuld.csv", "text/csv")
    st.subheader("Wat is gecontroleerd en opgeschoond?")
    gematcht = originele_antwoorden["track_id"].notna().sum()
    st.write(f"**Koppeling:** eerst Spotify-ID, daarna titel + artiest voor nog niet gekoppelde antwoorden. "
             f"{len(antwoorden)} oorspronkelijke antwoorden leverden {len(df)} mergerijen op; "
             f"{gematcht} antwoorden hadden voor de API-aanvulling een Spotify-datasetmatch. Meerdere matches verklaren de extra rijen.")
    st.write(f"**Spotify:** {broninfo['spotify_bronrijen']:,} bronrijen → "
             f"{broninfo['spotify_gebruikt']:,} bruikbare rijen. Eén rij zonder bruikbare speelduur "
             "is uitgesloten. Nulwaarden bij tempo zijn bewust behouden; ze zijn niet automatisch fout.")
    st.write("**Ontbrekende waarden:** genres en vier audiokenmerken direct aangevuld in de bestaande kolommen, met bronvermelding. "
             "Studentenmetingen zijn niet geschat of uit de eindtabel verwijderd. "
             "Elke grafiek gebruikt alleen de velden die hij nodig heeft en vermeldt het aantal bruikbare antwoorden.")
    st.write("**Dubbele rijen:** behouden in df. In grafiektabellen telt een oorspronkelijk antwoord eenmaal, "
             "of eenmaal per genre. Zo krijgen extra matches geen extra gewicht. "
             "De losse Spotify-ranglijst beschrijft juist alle bronrijen.")
    st.write("**Keuze van variabelen:** muziekvoorkeur, genre, audiokenmerken en de drie uitkomsten dragen het verhaal. "
             "Studiecontext en studietaak helpen andere verklaringen te bekijken. Overige persoonsgegevens "
             "en vrije tekst zijn niet nodig voor deze vergelijkingen.")

    st.write("Ontbrekende waarden en geobserveerde bereiken in de volledige eindtabel:")
    numeriek = df.select_dtypes(include="number")
    kwaliteit = pd.DataFrame({
        "Ontbrekend": df.isna().sum(), "Ontbrekend (%)": (df.isna().mean() * 100).round(1),
        "Minimum": numeriek.min(), "Maximum": numeriek.max()
    })
    st.dataframe(kwaliteit)
    st.caption(f"Eindtabel: {len(df)} rijen, {len(df.columns)} kolommen; "
               f"{df.duplicated().sum()} volledig identieke extra rijen zijn behouden. "
               "De tabel telt mergerijen, niet unieke deelnemers.")
    buiten_bereik = ((df[["energy", "valence", "danceability"]] < 0)
                    | (df[["energy", "valence", "danceability"]] > 1)).sum().sum()
    st.write(f"Bereikcheck: {buiten_bereik} waarden buiten 0–1 bij energy, valence en danceability; "
             f"{int((df['tempo'] < 0).sum())} negatieve tempo's. Ontbrekende waarden tellen hierboven apart mee.")
    with st.expander("Bekijk de volledige eindtabel"):
        st.dataframe(df, hide_index=True)
    with st.expander("Bronnen en werkwijze"):
        st.markdown((map_dashboard / "BRONNEN.md").read_text(encoding="utf-8"))

st.divider()
st.subheader("Conclusie")
lager = int((vergelijking["Verschil"] < 0).sum())
st.write(f"Bij {lager} van de {len(vergelijking)} genres is de gemiddelde voorkeur tijdens studeren lager "
         f"dan bij dagelijks luisteren. Het grootste verschil zien we bij {grootste} ({verschil:+.2f} punten). "
         "De gekoppelde ervaringen leveren veel minder geldige antwoorden op. Ze laten patronen zien, "
         "maar onderbouwen geen uitspraak dat een bepaald genre energie, stemming of studieprestaties verbetert.")
