"""Firestore tools for querying and managing the running shoes and gear catalog."""

from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Hardcoded project ID as string to avoid project number issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-e75d23b408af"
COLLECTION_NAME = "shoes"


def _get_db() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def list_shoes(category: Optional[str] = None, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
    """List running shoes from the catalog, optionally filtering by category or maximum price.

    Args:
        category: Optional category or shoe type (e.g., 'Daily Trainer', 'Race Day', 'Max Cushion', 'Tempo').
        max_price: Optional maximum price in USD.

    Returns:
        A list of shoes matching the query criteria.
    """
    db = _get_db()
    shoes_ref = db.collection(COLLECTION_NAME)
    docs = shoes_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if category and category.lower() not in data.get("category", "").lower() and category.lower() not in data.get("name", "").lower():
            continue
        if max_price is not None and data.get("price", 0) > max_price:
            continue
        results.append(data)

    return results


def get_shoe_details(shoe_id_or_name: str) -> Dict[str, Any]:
    """Retrieve detailed specifications and recommendations for a specific shoe by ID or name.

    Args:
        shoe_id_or_name: The shoe ID (e.g., 'vaporfly-3', 'ghost-16') or part of its name.

    Returns:
        The shoe record dictionary, or an error message if not found.
    """
    db = _get_db()
    # First try direct document lookup by ID
    doc_ref = db.collection(COLLECTION_NAME).document(shoe_id_or_name.lower().strip())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()

    # Fallback to search by name substring
    query = shoe_id_or_name.lower().strip()
    docs = db.collection(COLLECTION_NAME).stream()
    for d in docs:
        data = d.to_dict()
        if query in data.get("name", "").lower() or query in data.get("id", "").lower():
            return data

    return {"error": f"No shoe found matching '{shoe_id_or_name}' in the catalog."}


def add_or_update_shoe(
    shoe_id: str,
    name: str,
    brand: str,
    category: str,
    price: float,
    weight_oz: float,
    drop_mm: float,
    cushion_level: str,
    best_for: str,
    in_stock: bool = True,
    rating: float = 4.5,
) -> Dict[str, Any]:
    """Add a new shoe or update an existing shoe in the PaceCraft catalog.

    Args:
        shoe_id: Unique slug identifier for the shoe (e.g. 'superblast-2').
        name: Full product name (e.g. 'ASICS Superblast 2').
        brand: Brand name (e.g. 'ASICS').
        category: Shoe classification (e.g. 'Super Trainer', 'Racing', 'Daily Trainer').
        price: Price in USD.
        weight_oz: Weight in ounces.
        drop_mm: Heel-to-toe drop in millimeters.
        cushion_level: Cushioning category (e.g. 'Max', 'Medium', 'Plush').
        best_for: Description of target runner use-cases or workouts.
        in_stock: Whether the item is currently in stock.
        rating: Average review rating (1.0 to 5.0).

    Returns:
        Confirmation dictionary indicating success.
    """
    db = _get_db()
    shoe_data = {
        "id": shoe_id.lower().strip(),
        "name": name,
        "brand": brand,
        "category": category,
        "price": price,
        "weight_oz": weight_oz,
        "drop_mm": drop_mm,
        "cushion_level": cushion_level,
        "best_for": best_for,
        "in_stock": in_stock,
        "rating": rating,
    }
    db.collection(COLLECTION_NAME).document(shoe_data["id"]).set(shoe_data)
    return {"status": "success", "message": f"Saved {name} to catalog.", "shoe": shoe_data}
