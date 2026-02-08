from sentence_transformers import SentenceTransformer
import json
import numpy as np
from qdrant_client import QdrantClient
import os
from qdrant_client.models import (
    SparseVector,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    Prefetch,
    QueryRequest,
    FusionQuery
)
import torch
from dotenv import load_dotenv



# Load environment variables from .env file
load_dotenv()

# Initialize model
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Load vocabulary (assuming it's a list)
with open("parasave_vocabulary.json", "r", encoding="utf-8") as f:
    vocab = json.load(f)

# Initialize Qdrant client
client = QdrantClient(
    "https://f0c459b3-fc02-412f-b600-df3242a3c241.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key=os.getenv("QDRANT_API_KEY"),
)

def create_sparse_vector(ingredients_list, vocab, lambda_decay=0.65):
    """
    Create sparse vector from ingredients list.
    
    Args:
        ingredients_list: List of ingredients in order
        vocab: List of all unique ingredients (vocabulary)
        lambda_decay: Decay constant (default 0.65)
        
    Returns:
        SparseVector object for Qdrant
    """
    query_indices = []
    query_values = []
    
    for pos, ing in enumerate(ingredients_list, start=1):
        ing_lower = ing.strip().lower()
        
        # Find ingredient in vocabulary
        if ing_lower in vocab:
            idx = vocab.index(ing_lower)
            # ✅ CORRECT FORMULA: e^(-k * position)
            weight = float(np.exp(-lambda_decay * pos))
            query_indices.append(idx)
            query_values.append(weight)
    
    return SparseVector(indices=query_indices, values=query_values)


def search_products(
    query_text,
    query_ingredients,
    budget,
    category,
    vocab,
    model,
    client,
    lambda_decay=0.65,
    limit=10
):
    """
    Hybrid search with price and category filters.
    
    Args:
        query_text: Text representation of ingredients (for dense search)
        query_ingredients: List of ingredients (for sparse search)
        budget: Maximum price
        category: Product category
        vocab: Vocabulary list
        model: Sentence transformer model
        client: Qdrant client
        lambda_decay: Decay constant for scoring
        limit: Number of results to return
        
    Returns:
        Search results from Qdrant
    """
    
    # Create filter for price and category
    price_category_filter = Filter(
        must=[
            FieldCondition(
                key="price",
                range=Range(lte=float(budget))
            ),
            FieldCondition(
                key="category",
                match=MatchValue(value=category)
            )
        ]
    )
    
    # 1. Create dense vector
    query_dense = model.encode([query_text])[0].tolist()
    
    # 2. Create sparse vector
    query_sparse = create_sparse_vector(query_ingredients, vocab, lambda_decay)
    
    print(f"🔍 Searching with:")
    print(f"   Category: {category}")
    print(f"   Budget: ${budget}")
    print(f"   Ingredients: {len(query_ingredients)}")
    print(f"   Sparse vector non-zero: {len(query_sparse.indices)}")
    
    try:
        # 3. Hybrid search using query_points with prefetch
        response = client.query_points(
            collection_name="wellness_products",
            prefetch=[
                Prefetch(
                    query=query_dense,
                    using="dense",
                    limit=100,
                    filter=price_category_filter
                ),
                Prefetch(
                    query=query_sparse,
                    using="sparse",
                    limit=100,
                    filter=price_category_filter
                )
            ],
            query=FusionQuery(fusion="rrf"),  # RRF fusion
            limit=limit,
            with_payload=True
        )
        
        print(f"✅ Found {len(response.points) if hasattr(response, 'points') else 0} results")
        return response
        
    except Exception as e:
        print(f"❌ Error in search: {e}")
        print("   Trying fallback search with dense only...")
        
        # Fallback: dense search only
        try:
            response = client.search(
                collection_name="wellness_products",
                query_vector=("dense", query_dense),
                query_filter=price_category_filter,
                limit=limit,
                with_payload=True
            )
            print(f"✅ Fallback search found {len(response)} results")
            return response
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            raise


def get_alternatives(ingredients, category, budget):
    """
    Main function to get product alternatives.
    
    Args:
        ingredients: List of ingredient strings
        category: Product category
        budget: Maximum price
        
    Returns:
        List of alternative products
    """
    
    # Validate inputs
    if not ingredients:
        print("⚠️ No ingredients provided")
        return []
    
    if not category:
        print("⚠️ No category provided")
        return []
    
    # Clean ingredients (lowercase, strip)
    ingredients_clean = [ing.strip().lower() for ing in ingredients if ing.strip()]
    
    print(f"\n🔎 Searching alternatives:")
    print(f"   Ingredients: {ingredients_clean[:5]}...")
    print(f"   Category: {category}")
    print(f"   Budget: ${budget}")
    
    # Create query text for dense search
    query_text = ", ".join(ingredients_clean)
    
    # Perform search
    try:
        results = search_products(
            query_text=query_text,
            query_ingredients=ingredients_clean,
            budget=budget,
            category=category,
            vocab=vocab,
            model=model,
            client=client,
        )
        
        # Return points
        if hasattr(results, 'points'):
            return results.points
        else:
            return results
            
    except Exception as e:
        print(f"❌ Error in get_alternatives: {e}")
        return []

