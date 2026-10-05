# StreamVault — Environnement local

Ce dossier contient les éléments permettant d'exécuter l'environnement local de **StreamVault** :

- MongoDB
- Metabase
- le producteur Python de commandes envoyé vers Azure Event Hubs

## Docker

Le fichier `docker-compose.yml` démarre deux services :

- **MongoDB 8.0** sur le port `27017`
- **Metabase** sur le port `3000`

Les données MongoDB sont conservées dans le volume `mongo_data_sv`.

### Configuration

Créer un fichier `.env` contenant les variables nécessaires :

```env
MONGO_USERNAME=...
MONGO_PASSWORD=...
MONGO_URI=...
EVENT_HUB_CONNECTION_STRING=...
```

Le fichier `.env` ne doit pas être ajouté au dépôt Git.

### Démarrage

```bash
docker compose up -d
```

Pour arrêter les services :

```bash
docker compose down
```

Metabase est ensuite accessible localement sur le port `3000`.

---

## Producteur de commandes

Le fichier `producer.py` génère des commandes simulées et les envoie vers **Azure Event Hubs**.

À chaque génération, le script :

1. sélectionne aléatoirement un client dans la collection `clients` ;
2. sélectionne aléatoirement un média dans la collection `medias` ;
3. attribue un prix stable au média pendant l'exécution du script ;
4. génère un identifiant UUID et une date UTC ;
5. envoie la commande au format JSON vers Event Hubs ;
6. attend 3 secondes avant de générer la commande suivante.

Exemple de commande :

```json
{
  "_id": "uuid",
  "client_id": "id_client",
  "media_id": "id_media",
  "prix": 19.99,
  "date_commande": "2026-09-29T12:33:17+00:00"
}
```

Le producer vérifie au démarrage que les collections `clients` et `medias` contiennent des données.

### Lancement

Installer les dépendances nécessaires :

```bash
pip install pymongo azure-eventhub python-dotenv
```

Puis lancer :

```bash
python producer.py
```

Le script peut être arrêté avec `Ctrl + C`.

## Flux des commandes

```text
MongoDB (clients + medias)
          ↓
     producer.py
          ↓
 Azure Event Hubs
          ↓
     Consommateur
          ↓
         ADLS
          ↓
Azure Data Factory
          ↓
 MongoDB (commandes)
          ↓
       Metabase
```

## Sécurité

Les identifiants MongoDB et la chaîne de connexion Event Hubs sont chargés depuis les variables d'environnement et ne sont pas écrits directement dans le code.

Le fichier `.env` doit être exclu du dépôt :

```gitignore
.env
__pycache__/
*.pyc
```