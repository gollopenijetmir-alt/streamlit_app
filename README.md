# Raporti Automatik i Shitjeve (Streamlit)

Aplikacion Streamlit që i automatizon analizat nga Project 1 (EDA) për
menaxherin e shitjes: ngarkon xlsx, validon skemën, dhe shfaq 3 sllajde
(seksione) me KPI, grafikë dhe insight-e të llogaritura automatikisht.

## Si ta niosh lokalisht

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Hap browser-in te linku që shfaqet (zakonisht http://localhost:8501).

## Si ta provosh

1. Ngarko `sample_data/demo_skema_gabim.xlsx` → duhesh me pa mesazh gabimi
2. Ngarko `sample_data/demo_shitjet.xlsx` → duhesh me i pa 3 sllajdet
3. Ndrysho dropdown-at (periudha/shteti) → numrat dhe grafikët ndryshojnë

## Si ta provosh me file-in origjinal

Me `online_retail_II.xlsx` (45MB, s'është në repo — shiko `.gitignore`),
duhet me dal:

- **1,003,214 rreshta shitje**
- **19,104 rreshta kthime**

## Struktura

```
app.py                  # UI kryesore
pipeline/
  validate.py           # validimi i skemës
  clean.py              # pastrimi + ndarja e kthimeve
  aggregate.py           # agregimet për sllajdet
slides.py               # 3 sllajdet (grafikë + insight)
tests/test_pipeline.py  # pytest
```

## Testet

```bash
pytest
```

## Deploy

Streamlit Cloud → lidh repo-n → `app.py` si entry point → deploy.
Auto-deploy ndodh në çdo merge në `main`.
