# Website Monitor tool 🔍
Semplice script che verifica se un sito web è cambiato confrontando l'hash
sha256 precedente con quello nuovo.

I siti da monitorare devono essere elencati in `websites.csv` mettendo una 
virgola `,` dopo l'indirizzo. Lo script popola lo spazio dopo la `,` con
l'ultimo hash che ha calcolato.

Per avviare lo script è necessario installare le librerie elencati 
in `requirements.txt` tramite il comando `pip install -r requirements.txt`;
lo script è stato sviluppato con Python 3.7.7.

Lo script si utilizza avviandolo tramite python:
```shell script
python main.py
```