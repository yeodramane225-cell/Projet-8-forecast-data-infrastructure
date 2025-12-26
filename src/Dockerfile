# Utilise une image Python légère basée sur Debian Slim
FROM python:3.10-slim

# Définit le dossier de travail dans le conteneur
WORKDIR /app

# Copie tout le contenu du dossier src/ dans /app du conteneur
COPY . /app

# Installe les dépendances Python listées dans requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Commande par défaut (sera écrasée par docker-compose)
# Ici, on lance transform.py si aucune autre commande n'est fournie
CMD ["python3", "transform.py"]

