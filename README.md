# Kalkulator rachunku Tauron

## Narzędzie do obliczania miesięcznego rachunku za prąd od Tauron

- Aktualnie dostosowane pod taryfę dynamiczną + dystrybucję G13 przy rozliczeniu miesięcznym
- Zrobione według [Taryfy Dynamicznej](https://www.tauron.pl/-/media/offer-documents/produkty/2024/08-2024/dynamiczne/ts/EE-GD-CDzcb-Bezpieczny-TS-0.ashx), w tym repozytorum jest też kopia tego dokumentu (`taryfa_dynamiczna.pdf`)

## Setup: 
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## Jak używać:
 - Zaloguj się do serwisu eLicznik, wybierz cały miesiąc i pobierz dane w formacie CSV.
 - Wejdź na https://energy.instrat.pl/ceny/energia-rdn-godzinowe/ i pobierz wszystkie dane, zapisz jako `electricity_prices_day_ahead_hourly_all.csv` w tym samym folderze co program
- Uruchom `python3 calc.py Dane_eLicznik_xxx.csv`

## Rozbieżności
- Marginalne (na 5 miejscu po przecinku) rozbieżności w cenie jednostkowej za kWh mogą wynikać z innego sposobu obsługi liczb zmiennoprzecinkowych przez Tauron.
- Nieco większe rozbieżności występują ze względu na niezrozumiały dla mnie sposób zaokrąglania przez Tauron do pełnych kWh, np. zarówno 40.9 jak i 41.8 (odczytane z wykresu kołowego z eLicznik) zaokrąglają się u nich do 41 😂
