from flask import Flask, render_template, request
import requests
import pandas as pd
import matplotlib.pyplot as plt
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
        "unit-level": 2,      # 2 = województwa
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

def generuj_wykres(df):
    top = df.head(10)  # TOP 10 województw
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

@app.route('/mapa')
def mapa():
    return render_template("mapa.html")

@app.route('/login')
def login():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)
