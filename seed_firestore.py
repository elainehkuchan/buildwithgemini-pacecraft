"""Seed script for PaceCraft running shoes and gear catalog in Cloud Firestore."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-e75d23b408af"

SEEDED_SHOES = [
    {
        "id": "vaporfly-3",
        "name": "Nike Vaporfly 3",
        "brand": "Nike",
        "category": "Race Day / Carbon Plated",
        "price": 260,
        "weight_oz": 6.9,
        "drop_mm": 8,
        "cushion_level": "Max",
        "best_for": "Marathon and half-marathon racing, speed workouts",
        "in_stock": True,
        "rating": 4.8,
    },
    {
        "id": "ghost-16",
        "name": "Brooks Ghost 16",
        "brand": "Brooks",
        "category": "Daily Trainer / Neutral",
        "price": 140,
        "weight_oz": 9.5,
        "drop_mm": 12,
        "cushion_level": "Medium-High",
        "best_for": "Daily miles, long recovery runs, injury-prone knees",
        "in_stock": True,
        "rating": 4.7,
    },
    {
        "id": "endorphin-speed-4",
        "name": "Saucony Endorphin Speed 4",
        "brand": "Saucony",
        "category": "Tempo / Nylon Plated",
        "price": 170,
        "weight_oz": 8.2,
        "drop_mm": 8,
        "cushion_level": "High Responsive",
        "best_for": "Tempo runs, intervals, fast long runs",
        "in_stock": True,
        "rating": 4.9,
    },
    {
        "id": "clifton-9",
        "name": "Hoka Clifton 9",
        "brand": "Hoka",
        "category": "Max Cushion / Recovery",
        "price": 145,
        "weight_oz": 8.7,
        "drop_mm": 5,
        "cushion_level": "Max Plush",
        "best_for": "Recovery runs, plush daily comfort, plantar fasciitis relief",
        "in_stock": True,
        "rating": 4.6,
    },
    {
        "id": "adizero-boston-12",
        "name": "Adidas Adizero Boston 12",
        "brand": "Adidas",
        "category": "Workout Trainer / EnergyRods",
        "price": 160,
        "weight_oz": 9.2,
        "drop_mm": 6.5,
        "cushion_level": "Medium Firm",
        "best_for": "Marathon pace workouts, steady progression runs",
        "in_stock": False,
        "rating": 4.5,
    },
]


def seed_database():
    print(f"Connecting to Firestore with project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("shoes")

    for item in SEEDED_SHOES:
        doc_id = item["id"]
        collection_ref.document(doc_id).set(item)
        print(f"  ✓ Seeded: {item['name']} ({doc_id})")

    print("\nFirestore seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
