# ICU_Simulation
Dit project is een **agent-based simulation** van de Intensive Care (ICU), gemaakt met [Mesa](https://mesa.readthedocs.io/) en [Solara](https://solara.dev/).  
Het model simuleert patiëntenstromen, capaciteit, kosten en planning binnen de ICU, met de mogelijkheid om zowel interactief als batchgewijs simulaties uit te voeren.

---

## Projectstructuur

- `main.py`  
  Startpunt voor de interactieve visualisatie van het model met **Solara**.  
  Laat een gridweergave en grafieken zien van o.a. capaciteit.

- `batch_run.py`  
  Script voor het uitvoeren van meerdere runs in batchmodus.  
  Resultaten (CSV-bestanden) worden opgeslagen in de map `runs/`.

- `lib/model.py`  
  Implementatie van de **ICUModel** klasse.  
  Bevat logica voor patiënten, afdelingen, capaciteitsbeheer en kostenberekeningen.

- `lib/params.py`  
  Bevat instelbare **modelparameters** (zoals aantal patiënten, capaciteit, clock speed, etc.).  
  Ook een interactieve `NestedMultiSelect` component om groepen specialisaties in te stellen.

- `lib/utils.py`  
  Hulpfuncties:
  - `Clock`: houdt de tijd bij in de simulatie.
  - `DataManager`: laadt en verwerkt patiëntgegevens en covid-data.
  - `get_color`: kleurfunctie voor visualisatie.

- `lib/agents`  
  Bevat agentdefinities zoals `Patient`, `Frontdesk`, `Department`, en `Home`.

- `batch_run_config.json`  
  Configuratiebestand met parameterinstellingen voor batch runs.

- `runs/`  
  Map waarin resultaten van batchruns als CSV-bestanden worden opgeslagen.

---

## Installatie
Installeer dependencies (bij voorkeur in een virtuele omgeving):

pip install -r requirements.txt
Minimale dependencies:

mesa

solara

numpy

pandas

## Gebruik
Interactieve simulatie starten
Start de Solara-applicatie:

bash
Code kopiëren
solara run main.py
Open daarna de link in de browser (standaard: http://localhost:8765).

Batch run uitvoeren
Run meerdere simulaties tegelijk met verschillende parameterinstellingen:

python batch_run.py --time 7

Waarbij --time de duur van de simulatie aangeeft in dagen.
De resultaten (o.a. opnames.csv, capacity.csv, costs.csv) worden weggeschreven in ./runs/runX/.