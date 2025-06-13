from flask import Flask, render_template, request
import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import io
import base64


app = Flask(__name__)

# Stałe
VARIABLE_ID = 633692  # Średnia cena 1 m² mieszkań (ogółem)
LATA = [str(rok) for rok in range(2010, 2024)]


def pobierz_dane_wojewodztwa(rok):
    url = f"https://bdl.stat.gov.pl/api/v1/data/by-variable/{VARIABLE_ID}"
    params = {
        "aggregate-id": 1,
        "unit-level": 2,
        "year": rok,
        "page-size": 100
    }
    response = requests.get(url, params=params)
    data = response.json()

    wojewodztwa = []
    for wynik in data.get("results", []):
        nazwa = wynik.get("name", "")
        for wpis in wynik.get("values", []):
            if wpis.get("year") == rok and wpis.get("val") is not None:
                wojewodztwa.append({
                    "województwo": nazwa,
                    "wartość": wpis["val"]
                })

    df = pd.DataFrame(wojewodztwa)
    return df.sort_values(by="wartość", ascending=False)

def pobierz_dane_czasowe(wojewodztwo, lata):
    unit_id = MAPA_WOJ.get(wojewodztwo)
    if not unit_id:
        print(f"[Błąd] Nie znaleziono ID dla województwa: {wojewodztwo}")
        return pd.DataFrame()
    
    url = f"https://bdl.stat.gov.pl/api/v1/data/by-unit/{unit_id}"
    params = {
        "var-id": [VARIABLE_ID],
        "year": lata,
        "aggregate-id": 1,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Błąd API] {wojewodztwo} → {e}")
        return pd.DataFrame()

    dane = response.json()

    wartosci = []
    for wynik in dane.get("results", []):
        for wpis in wynik.get("values", []):
            if wpis["val"] is not None:
                wartosci.append({"rok": wpis["year"], "wartość": wpis["val"]})

    if not wartosci:
        print(f"[Info] Brak danych: {wojewodztwo}, lata: {lata}")

    return pd.DataFrame(wartosci).sort_values("rok")

def generuj_wykres(df):
    top = df.head(10)
    plt.figure(figsize=(10, 6))
    plt.barh(top["województwo"], top["wartość"], color='skyblue')
    plt.xlabel("Cena za 1m²")
    plt.title("Top 10 województw wg ceny 1m²")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    obrazek = io.BytesIO()
    plt.savefig(obrazek, format='png')
    obrazek.seek(0)
    plt.close()

    return base64.b64encode(obrazek.getvalue()).decode("utf-8")

def generuj_wykres_liniowy(df, wojewodztwo):
    plt.figure(figsize=(10, 5))
    plt.plot(df["rok"], df["wartość"], marker='o', color='green')
    plt.title(f"Zmiana ceny 1m² mieszkań – {wojewodztwo}")
    plt.xlabel("Rok")
    plt.ylabel("Cena (zł)")
    plt.grid(True)
    plt.tight_layout()

    obrazek = io.BytesIO()
    plt.savefig(obrazek, format='png')
    obrazek.seek(0)
    plt.close()
    return base64.b64encode(obrazek.getvalue()).decode("utf-8")

def pobierz_wojewodztwa():
    url = "https://bdl.stat.gov.pl/api/v1/units"
    params = {
        "level": 2,
        "format": "json",
        "page-size": 100
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    dane = response.json()["results"]
    
    mapa = {}
    for j in dane:
        nazwa = j["name"].strip().capitalize()  # np. "mazowieckie" → "Mazowieckie"
        mapa[nazwa] = j["id"]
    
    return mapa

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ranking', methods=["GET", "POST"])
def ranking():
    wybrany_rok = request.form.get("rok", "2023")
    df = pobierz_dane_wojewodztwa(wybrany_rok)
    wykres = generuj_wykres(df)
    return render_template("ranking.html", tabela=df, wykres=wykres, lata=LATA, aktualny_rok=wybrany_rok)

@app.route('/wykres')
def wykres():
    return render_template("wykres.html")

@app.route("/trend", methods=["GET", "POST"])
def trend():
    wykres = None
    blad = None
    aktualne_woj = "Mazowieckie"

    if request.method == "POST":
        aktualne_woj = request.form.get("wojewodztwo")
        od = int(request.form.get("od", 2010))
        do = int(request.form.get("do", 2023))

        if od > do:
            blad = f"Nieprawidłowy zakres lat: {od} > {do}"
        else:
            lata_wybrane = [str(r) for r in range(od, do + 1)]
            df = pobierz_dane_czasowe(aktualne_woj, lata_wybrane)
            if not df.empty:
                wykres = generuj_wykres_liniowy(df, aktualne_woj)

    return render_template("trend.html", lata=LATA, aktualne_woj=aktualne_woj, wykres=wykres, blad=blad)

MAPA_WOJ = pobierz_wojewodztwa()

@app.route('/login')
def login():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)
