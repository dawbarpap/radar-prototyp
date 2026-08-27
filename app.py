# -*- coding: utf-8 -*-
"""
app.py — prosty panel Streamlit (celowo brzydki :)):
1) edycja pytań (zapis questions.yaml prosto do repo na GitHubie),
2) ręczne uruchomienie odpytywania (workflow_dispatch),
3) podgląd zebranych odpowiedzi.

Wymaga w .streamlit/secrets.toml:
GITHUB_TOKEN = "ghp_..."   # token z uprawnieniem repo + workflow
GITHUB_REPO  = "twoja-organizacja/radar-prototyp"
"""
import base64
import requests
import streamlit as st
import yaml

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]
API = f"https://api.github.com/repos/{REPO}"
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

st.title("RadarAI — prototyp odpytywania modeli")
st.caption(f"Repozytorium: {REPO} · odpowiedzi trafiają do katalogu answers/ jako pliki .txt")

# ---------- 1. PYTANIA ----------
st.header("1. Pytania i konfiguracja")
r = requests.get(f"{API}/contents/questions.yaml", headers=H)
r.raise_for_status()
plik = r.json()
tresc = base64.b64decode(plik["content"]).decode("utf-8")

nowa = st.text_area("questions.yaml (pytania, modele, powtórzenia)", tresc, height=380)
if st.button("Zapisz konfigurację do repo"):
    try:
        yaml.safe_load(nowa)  # walidacja przed zapisem
    except Exception as e:
        st.error(f"To nie jest poprawny YAML: {e}")
    else:
        w = requests.put(
            f"{API}/contents/questions.yaml",
            headers=H,
            json={
                "message": "Aktualizacja pytań z panelu Streamlit",
                "content": base64.b64encode(nowa.encode("utf-8")).decode(),
                "sha": plik["sha"],
            },
        )
        st.success("Zapisano.") if w.ok else st.error(w.text)


st.subheader("Albo wgraj pytania w Excelu")
st.write("Plik `questions.xlsx`, kolumny: **id**, **pytanie** (pierwszy wiersz = nagłówki). "
         "Jeśli plik istnieje w repo, ma pierwszeństwo przed listą w YAML.")
xls = st.file_uploader("questions.xlsx", type=["xlsx"])
if xls is not None and st.button("Zapisz Excel do repo"):
    dane = xls.read()
    r_old = requests.get(f"{API}/contents/questions.xlsx", headers=H)
    payload = {"message": "Pytania z pliku Excel (panel Streamlit)",
               "content": base64.b64encode(dane).decode()}
    if r_old.status_code == 200:
        payload["sha"] = r_old.json()["sha"]
    w = requests.put(f"{API}/contents/questions.xlsx", headers=H, json=payload)
    st.success("Zapisano questions.xlsx.") if w.ok else st.error(w.text)

# ---------- 2. URUCHOMIENIE ----------
st.header("2. Uruchomienie")
st.write("Harmonogram (cron) ustawia się w pliku `.github/workflows/poll.yml`. "
         "Tu można dodatkowo odpalić przebieg od ręki:")
if st.button("Uruchom odpytywanie TERAZ"):
    w = requests.post(
        f"{API}/actions/workflows/poll.yml/dispatches",
        headers=H,
        json={"ref": "main"},
    )
    if w.status_code == 204:
        st.success("Wystartowało. Wyniki pojawią się w answers/ po kilku minutach.")
    else:
        st.error(w.text)

# ---------- 3. PODGLĄD ODPOWIEDZI ----------
st.header("3. Odpowiedzi")
r = requests.get(f"{API}/contents/answers", headers=H)
if r.status_code == 404:
    st.info("Brak jeszcze odpowiedzi — uruchom pierwszy przebieg.")
else:
    przebiegi = sorted([x["name"] for x in r.json() if x["type"] == "dir"], reverse=True)
    wybor = st.selectbox("Przebieg", przebiegi)
    if wybor:
        r2 = requests.get(f"{API}/contents/answers/{wybor}", headers=H)
        pliki = [x for x in r2.json() if x["name"].endswith(".txt")]
        st.write(f"Plików: {len(pliki)}")
        for x in pliki:
            with st.expander(x["name"]):
                zawartosc = base64.b64decode(
                    requests.get(x["url"], headers=H).json()["content"]
                ).decode("utf-8")
                st.text(zawartosc)
