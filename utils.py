from sentence_transformers import SentenceTransformer
import json
import numpy as np
from qdrant_client import QdrantClient
import os
from qdrant_client.models import (
    NamedVector,
    SparseVector,
    NamedSparseVector,
    RecommendInput,
    VectorStruct,
    Fusion,
)
import torch
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from dotenv import load_dotenv
load_dotenv()

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device) 
vocab = json.load(open("parasave_vocabulary.json"))
client = QdrantClient(
    "https://f0c459b3-fc02-412f-b600-df3242a3c241.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key=os.getenv("QDRANT_API_KEY"),
)


def search_products(
    query_text, query_ingredients, budget, category, vocab, model, client, lambda_decay=0.65
):
    
    price_category_filter = Filter(
    must=[
        # Price ≤ budget
        FieldCondition(
            key="price",
            range=Range(lte=budget) 
        ),
        # Category exact match
        FieldCondition(
            key="category", 
            match=MatchValue(value=category) 
        )
        ]
    )
    # Dense
    query_dense = model.encode([query_text])[0].tolist()
    # Sparse
    query_indices, query_values = [], []
    for pos, ing in enumerate(query_ingredients, 1):
        if ing in vocab:
            idx = vocab.index(ing)
            weight = np.exp(-lambda_decay * (pos - 1))
            query_indices.append(idx)
            query_values.append(weight)

    query_sparse = SparseVector(indices=query_indices, values=query_values)
    # Hybrid search
    response = client.query_points(
        collection_name="products",
        query=NamedVector(name="dense", vector=query_dense),
        query_sparse=[NamedSparseVector(name="sparse", vector=query_sparse)],
        filter=Filter( 
            must=[
                FieldCondition(key="price", range=Range(lte=budget)),
                FieldCondition(key="category", match=MatchValue(value=category))
            ]
        ),
        limit=10,
        score=RecommendInput( 
            fusion=Fusion.RRF
        )
    )

    return response

def get_alternatives( ingredients, category, budget):
    query_text = ", ".join(ingredients)
    results = search_products(
        query_text=query_text,
        query_ingredients=ingredients,
        budget=budget,
        category=category,
        vocab=vocab,
        model=model,
        client=client,
    )
    filtered_results = []
    for item in results:
        item_category = item.payload.get("category", "").lower()
        item_price = item.payload.get("price", float('inf'))
        if item_category == category.lower() and item_price <= budget:
            filtered_results.append(item)
    return filtered_results


#example
# results = search_products(
#     query_text="Aqua, Ethylhexyl Salicylate, Methylene Bis-Benzotriazolyl Tetramethylbutylphenol",  # Parse from query
#     query_ingredients=["Aqua", "Ethylhexyl Salicylate", "Methylene Bis-Benzotriazolyl Tetramethylbutylphenol"],  # Parse from query
#     budget=30.0,
#     category="solar",
#     vocab=vocab,
#     model=model,
#     client=client,
# )
