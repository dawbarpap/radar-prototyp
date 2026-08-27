# RadarAI — prototyp cyklicznego odpytywania modeli AI

Prosty prototyp: pytania definiujesz w panelu, GitHub Actions odpytuje modele
w zadanych interwałach, odpowiedzi lądują jako pliki `.txt` w repozytorium.

Architektura (celowo minimalna):
- `questions.yaml` — pytania, lista modeli, liczba powtórzeń
- `poller.py` — skrypt odpytujący (OpenRouter: jeden klucz, wiele modeli)
- `.github/workflows/poll.yml` — harmonogram (cron) + uruchamianie ręczne
- `app.py` — panel Streamlit: edycja pytań, przycisk „uruchom teraz", podgląd odpowiedzi
- `answers/RRRR-MM-DD_GG-MM/` — wyniki, po jednym pliku na parę pytanie×model

## Krok 1 — repozytorium na GitHubie
1. Załóż nowe repozytorium (może być prywatne), np. `radar-prototyp`.
2. Wgraj do niego wszystkie pliki z tej paczki (struktura bez zmian).
3. Upewnij się, że gałąź główna nazywa się `main` (albo popraw `ref` w `app.py`).

## Krok 2 — klucze do modeli
Odpowiedzi mają odzwierciedlać to, co widzi użytkownik wersji przeglądarkowej,
dlatego każdy model odpytujemy przez jego natywne API z WŁĄCZONYM oficjalnym
wyszukiwaniem internetowym. Potrzebne klucze (sekrety w Settings → Secrets → Actions):

| Sekret | Skąd | Co obsługuje |
|---|---|---|
| `OPENAI_API_KEY` | platform.openai.com | ChatGPT (Responses API + web_search) |
| `ANTHROPIC_API_KEY` | console.anthropic.com | Claude (web_search_20250305) |
| `GEMINI_API_KEY` | aistudio.google.com | Gemini (Google Search grounding) |
| `PERPLEXITY_API_KEY` | perplexity.ai/settings/api | Perplexity sonar |
| `XAI_API_KEY` | console.x.ai | Grok (Agent Tools web_search) |
| `OPENROUTER_API_KEY` | openrouter.ai | przybliżenia: Meta AI, Mistral, DeepSeek |

Brak któregoś klucza nie wywala przebiegu — dany model dostaje status POMINIĘTO.
Identyfikatory modeli w `questions.yaml` sprawdź w dokumentacji dostawców,
bo zmieniają się co kilka miesięcy.

## Krok 3 — pierwszy przebieg (test bez czekania na cron)
1. Zakładka Actions → „Odpytywanie modeli AI" → Run workflow.
2. Po 2–5 minutach w katalogu `answers/` pojawi się folder z plikami `.txt`.
3. Każdy plik ma nagłówek z metryką (pytanie, model, data UTC, status) i pełną odpowiedź.

## Krok 4 — interwał
Interwał ustawia jedna linia w `.github/workflows/poll.yml`:
```
- cron: "0 */6 * * *"    # co 6 godzin
```
Przykłady: `"0 6 * * *"` = codziennie 6:00 UTC, `"0 6 * * 1"` = w poniedziałki,
`"0 */12 * * *"` = co 12 godzin. Uwaga: GitHub wykonuje crony z możliwym
opóźnieniem kilku–kilkunastu minut; harmonogram działa dopiero po wgraniu
pliku na gałąź główną.

## Krok 5 — panel Streamlit
1. Wygeneruj token GitHub: Settings (konto) → Developer settings →
   Personal access tokens → Fine-grained; dostęp do tego repozytorium,
   uprawnienia: Contents (Read and write) oraz Actions (Read and write).
2. Wejdź na https://share.streamlit.io, wskaż repozytorium i plik `app.py`.
3. W ustawieniach aplikacji (Secrets) wklej:
   ```
   GITHUB_TOKEN = "github_pat_..."
   GITHUB_REPO  = "twoja-nazwa/radar-prototyp"
   ```
4. Panel pozwala: edytować `questions.yaml` (z walidacją), odpalić przebieg
   od ręki i przeglądać zebrane odpowiedzi.

## Test lokalny (opcjonalnie)
```
pip install -r requirements.txt
python poller.py --mock            # bez API, generuje pliki testowe
OPENAI_API_KEY=... ANTHROPIC_API_KEY=... python poller.py   # naprawdę odpytuje
streamlit run app.py               # panel lokalnie (sekrety w .streamlit/secrets.toml)
```

## Ograniczenia prototypu (świadome)
- ChatGPT, Claude, Gemini, Perplexity i Grok odpowiadają z natywnym wyszukiwaniem —
  ta sama warstwa „model + wyszukiwarka" co w przeglądarce, choć wersja czatowa może
  mieć inny prompt systemowy, więc drobne różnice stylu są normalne.
- Meta AI nie udostępnia API konsumenckiego, a DeepSeek i Mistral nie wystawiają
  wyszukiwania w API — te trzy realizujemy jako jawnie oznaczone PRZYBLIŻENIE
  (OpenRouter + wtyczka web). W raportach traktować osobno.
- Brak analizy odpowiedzi — tylko zbieranie. Analizę robimy osobno (albo w Claude).
- GitHub Actions na darmowym planie w repo prywatnym ma limit 2000 minut/mies. —
  przy tym wolumenie wystarcza z ogromnym zapasem.
