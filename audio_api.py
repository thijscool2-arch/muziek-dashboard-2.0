"""ReccoBeats: openbare audiokenmerken per Spotify-track-ID, zonder token.

Bron: https://reccobeats.com/docs/apis/get-audio-features
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

KENMERKEN = ["energy", "valence", "tempo", "danceability"]


def spotify_id(waarde):
    match = re.fullmatch(r"(?:spotify:track:|https://open.spotify.com/track/)?([A-Za-z0-9]{22})(?:\?[^\s]*)?", str(waarde).strip())
    return match.group(1) if match else None


def track_ids(df):
    # Een bestaande Spotify-match heeft voorrang boven een ander ingevuld ID.
    return df["track_id"].map(spotify_id).fillna(df["Spotify ID"].map(spotify_id))


def haal_audio_op(df, cache, voortgang=None, ververs=False):
    ids = track_ids(df).dropna().unique().tolist()
    if not ververs:
        ids = [i for i in ids if i not in cache or cache[i].get("status", "").startswith("API")]
    nieuw = dict(cache)
    # Kleine batches; de API geeft de koppelsleutel terug, niet noodzakelijk in dezelfde volgorde.
    for start in range(0, len(ids), 20):
        batch = ids[start:start + 20]
        url = "https://api.reccobeats.com/v1/audio-features?ids=" + ",".join(batch)
        verzoek = Request(url, headers={"User-Agent": "MuziekDashboard/1.0"})
        resultaten = None
        for poging in range(3):
            try:
                with urlopen(verzoek, timeout=20) as antwoord:
                    resultaten = json.load(antwoord)["content"]
                break
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as fout:
                if poging == 2:
                    break
                wachttijd = 5 * (poging + 1)
                if isinstance(fout, HTTPError):
                    if fout.code not in (429, 500, 502, 503, 504):
                        break
                    retry_after = fout.headers.get("Retry-After", "5")
                    wachttijd = max(wachttijd, int(retry_after) if retry_after.isdigit() else 5)
                time.sleep(wachttijd)
        nu = datetime.now(timezone.utc).isoformat()
        if resultaten is None:
            for key in batch:
                nieuw.setdefault(key, {"status": "API niet bereikbaar"})
        else:
            gevonden = {spotify_id(r.get("href")): r for r in resultaten}
            for key in batch:
                r = gevonden.get(key, {})
                waarden = {}
                for k in KENMERKEN:
                    v = r.get(k)
                    if isinstance(v, (int, float)) and pd.notna(v) and v >= 0 and (k == "tempo" or v <= 1):
                        waarden[k] = v
                nieuw[key] = {"status": "Match" if waarden else "Geen kenmerken gevonden",
                              "opgehaald_op": nu, "bron_url": url,
                              "reccobeats_id": r.get("id"), **waarden}
        if voortgang:
            voortgang(min(start + 20, len(ids)), len(ids), nieuw)
        time.sleep(1)
    return nieuw


def audio_voor_grafiek(df, cache):
    # Eén bron per grafiek: uitsluitend de kenmerken uit ReccoBeats.
    resultaat = df.copy()
    resultaat["track_id"] = track_ids(df)
    for k in KENMERKEN:
        resultaat[k] = resultaat["track_id"].map(lambda key: cache.get(key, {}).get(k))
        resultaat[k] = pd.to_numeric(resultaat[k], errors="coerce")
    return resultaat


def vul_audio_aan(df, cache):
    resultaat = df.copy()
    nieuw = audio_voor_grafiek(df, cache)
    for k in KENMERKEN:
        resultaat[k] = df[k].fillna(nieuw[k])
    toegevoegd = pd.DataFrame({k: df[k].isna() & nieuw[k].notna() for k in KENMERKEN}).any(axis=1)
    resultaat["Aanvulling audiobron"] = pd.Series(pd.NA, index=df.index, dtype="string")
    resultaat.loc[toegevoegd, "Aanvulling audiobron"] = "ReccoBeats"
    resultaat.loc[toegevoegd, "track_id"] = resultaat.loc[toegevoegd, "track_id"].fillna(nieuw.loc[toegevoegd, "track_id"])
    return resultaat


if __name__ == "__main__":
    from muziek_api import lees_cache
    map_data = Path(__file__).resolve().parent
    pad = map_data / "reccobeats_cache.json"

    def opslaan(i, totaal, cache):
        pad.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{i}/{totaal} track-ID's gecontroleerd", flush=True)

    cache = haal_audio_op(pd.read_csv(map_data / "dashboard_data.csv"), lees_cache(pad), opslaan)
    pad.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
