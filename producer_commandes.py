import json
import random
import time
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

from pymongo import MongoClient
from azure.eventhub import EventHubProducerClient, EventData


# CONFIGURATION

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
EVENT_HUB_CONNECTION_STRING = os.getenv("EVENT_HUB_CONNECTION_STRING")


# CONNEXION À MONGODB

mongo_client = MongoClient(MONGO_URI)

db = mongo_client["streamvault"]

clients_collection = db["clients"]
medias_collection = db["medias"]


# VÉRIFICATION DES DONNÉES

if clients_collection.count_documents({}) == 0:
    raise Exception("Aucun client trouvé dans MongoDB.")

if medias_collection.count_documents({}) == 0:
    raise Exception("Aucun média trouvé dans MongoDB.")

print("Clients et médias disponibles.")


# PRIX STABLE PAR TITRE

prix_medias = {}


# CONNEXION À AZURE EVENT HUB

producer = EventHubProducerClient.from_connection_string(
    conn_str=EVENT_HUB_CONNECTION_STRING
)


# PRODUCTION DES COMMANDES

print("Producteur démarré...")

try:

    while True:

        # Récupère un client aléatoire
        client = next(
            clients_collection.aggregate([
                {"$sample": {"size": 1}}
            ])
        )

        # Récupère un média aléatoire
        media = next(
            medias_collection.aggregate([
                {"$sample": {"size": 1}}
            ])
        )

        media_id = str(media["_id"])

        # Attribue un prix au média uniquement
        # s'il n'en possède pas encore pendant cette exécution
        if media_id not in prix_medias:
            prix_medias[media_id] = round(
                random.uniform(5.0, 30.0),
                2
            )

        commande = {
            "_id": str(uuid.uuid4()),
            "client_id": str(client["_id"]),
            "media_id": media_id,
            "prix": prix_medias[media_id],
            "date_commande": datetime.now(timezone.utc).isoformat()
        }

        event_data_batch = producer.create_batch()

        event_data_batch.add(
            EventData(json.dumps(commande))
        )

        producer.send_batch(event_data_batch)

        print("Commande envoyée :")
        print(commande)

        time.sleep(3)


except KeyboardInterrupt:
    print("\nArrêt du producteur.")


finally:
    producer.close()
    mongo_client.close()