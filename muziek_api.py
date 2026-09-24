"""Genres ophalen via Apple's openbare iTunes Search API; geen token nodig.

Bron: https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html
Alleen titel en artiest worden verstuurd. Studentenmetingen blijven lokaal.
"""
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


def herstel_tekst(tekst):
    tekst = str(tekst).strip()
    # Een deel van de brontitels heeft verkeerd ingelezen UTF-8-tekens.
    try:
        return tekst.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return tekst


def normaal(tekst):
    tekst = unicodedata.normalize("NFKD", herstel_tekst(tekst)).casefold()
    tekst = "".join(c for c in tekst if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", "", tekst)


def sleutel(titel, artiest):
    return normaal(titel) + "|" + normaal(artiest)


def lees_cache(pad):
    return json.loads(pad.read_text(encoding="utf-8")) if pad.exists() else {}


def zoek_genre(titel, artiest):
    params = {"term": f"{herstel_tekst(titel)} {herstel_tekst(artiest)}",
              "entity": "song", "country": "NL", "limit": 50}
    url = "https://itunes.apple.com/search?" + urlencode(params)
    verzoek = Request(url, headers={"User-Agent": "MuziekDashboard/1.0"})
    for poging in range(3):
        try:
            with urlopen(verzoek, timeout=15) as antwoord:
                resultaten = json.load(antwoord)["results"]
            break
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as fout:
            if poging == 2:
                return {"status": "API niet bereikbaar", "genre": None}
            wachttijd = 5 * (poging + 1)
            if isinstance(fout, HTTPError):
                if fout.code not in (429, 500, 502, 503, 504):
                    return {"status": f"API-fout {fout.code}", "genre": None}
                retry_after = fout.headers.get("Retry-After", "5")
                wachttijd = max(wachttijd, int(retry_after) if retry_after.isdigit() else 5)
            time.sleep(wachttijd)

    # Geen fuzzy matching: live/remix/cover/versie moet ook in de titel kloppen.
    matches = [r for r in resultaten
               if normaal(r.get("trackName", "")) == normaal(titel)
               and normaal(r.get("artistName", "")) == normaal(artiest)
               and r.get("primaryGenreName")]
    genres = {r["primaryGenreName"] for r in matches}
    uitkomst = {"status": "Geen eenduidige match", "genre": None,
                "opgehaald_op": datetime.now(timezone.utc).isoformat(), "zoek_url": url}
    if len(genres) == 1:
        match = sorted(matches, key=lambda r: r["trackId"])[0]
        uitkomst.update(status="Match", genre=match["primaryGenreName"],
                        titel=match["trackName"], artiest=match["artistName"],
                        itunes_id=match["trackId"], bron_url=match.get("trackViewUrl"))
    return uitkomst


def haal_genres_op(df, cache, voortgang=None, ververs=False):
    # Eén aanvraag per unieke titel-artiestcombinatie; geen rijen uit df verwijderen.
    nummers = df.loc[df["track_genre"].isna(), ["Nummer", "Artiest"]].dropna().copy()
    nummers["sleutel"] = [sleutel(t, a) for t, a in nummers.itertuples(index=False, name=None)]
    nummers = nummers.drop_duplicates("sleutel")
    if not ververs:
        nummers = nummers[~nummers["sleutel"].isin(
            k for k, v in cache.items() if v.get("status") in ("Match", "Geen eenduidige match"))]
    nieuw = dict(cache)
    for i, (titel, artiest, key) in enumerate(nummers.itertuples(index=False, name=None), 1):
        resultaat = zoek_genre(titel, artiest)
        # Bij storing blijft een eerder succesvol resultaat beschikbaar.
        if not resultaat["status"].startswith("API") or key not in nieuw:
            nieuw[key] = resultaat
        if voortgang:
            voortgang(i, len(nummers), nieuw)
        time.sleep(3.2)  # Minder dan Apple's circa 20 verzoeken per minuut.
    return nieuw


def vul_genres_aan(df, cache):
    resultaat = df.copy()
    genres = []
    for titel, artiest in df[["Nummer", "Artiest"]].itertuples(index=False, name=None):
        match = cache.get(sleutel(titel, artiest), {}) if pd.notna(titel) and pd.notna(artiest) else {}
        genres.append(match.get("genre") if match.get("status") == "Match" else None)
    resultaat["track_genre"] = df["track_genre"].fillna(pd.Series(genres, index=df.index))
    resultaat["Genrebron"] = pd.Series(pd.NA, index=df.index, dtype="string")
    resultaat.loc[df["track_genre"].notna(), "Genrebron"] = "Spotify"
    resultaat.loc[df["track_genre"].isna() & resultaat["track_genre"].notna(), "Genrebron"] = "iTunes"
    return resultaat


if __name__ == "__main__":
    map_data = Path(__file__).resolve().parent
    pad = map_data / "itunes_cache.json"

    def opslaan(i, totaal, cache):
        pad.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        matches = sum(r.get("status") == "Match" for r in cache.values())
        print(f"{i}/{totaal} opgezocht; {matches} unieke nummers met genre", flush=True)

    df = pd.read_csv(map_data / "dashboard_data.csv")
    cache = haal_genres_op(df, lees_cache(pad), voortgang=opslaan)
    pad.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Ontbrekende genres:", df.track_genre.isna().sum(), "->",
          vul_genres_aan(df, cache)["track_genre"].isna().sum())
