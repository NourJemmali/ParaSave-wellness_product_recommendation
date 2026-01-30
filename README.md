# ParaSave: Wellness products recommendation
## 🔍 Project Overview

**ParaSave** consults you on the wellness product alternatives you should buy. Upload two photos and tell us about your preference. We'll find you safer, smarter, cheaper options.

### How It Works

**Inputs:**
1. **Photo of the product** - Shows the product name, brand... (usually the front) 📸
2. **Photo of the ingredients list** - The detailed ingredient label (usually on the back) 📸
3. **Budget** 📊

**Outputs:**
- **Alternative products** that match the original's effectiveness
- Detailed explanations for each recommendation

---

## 🎯 Objectives

**ParaSave** addresses critical gaps in wellness product shopping:
- **Ingredient Intelligence** - Understand complex ingredient lists and identify what actually matters
- **Budget Optimization** - Find cheaper alternatives with the same active ingredients
- **Transparent Recommendations** - Explain why each alternative works through clear
---

## 🛠️ Technologies Used

### **Core Development**
- **Python** `3.8.10` - Primary programming language

### **Data Collection & Processing**
- **Selenium** - Web scraping automation
- **BeautifulSoup** - HTML parsing and data extraction
- **Data Storage Formats**: JSON and `.pkl` (pickle)

### **AI & Machine Learning**
- **Groq API** - Vision-Language Model inference
  - Model: `meta-llama/llama-4-scout-17b-16e-instruct`
- **sentence-transformers** - Text embeddings
  - Model: `paraphrase-multilingual-MiniLM-L12-v2`
  - Embedding dimension: 384

### **Vector Database**
- **Qdrant Cloud** - Managed vector similarity search engine
- **qdrant-client** - Python client for Qdrant operations

### **Frontend**
- **Streamlit** `1.22.0` - Web application framework

## Architecture
```mermaid
flowchart TB
 subgraph subGraph1["Processing Layer"]
        OCR["VLM<br>(Visual Language Model)"]
        EMBED["Embedding Generator<br>"]
        INGR["Ingredient Scoring"]
  end
 subgraph subGraph2["Qdrant Vector Database"]
        QDRANT[("Qdrant Collection<br>wellness_products")]
        VEC2["weighted_ingredients<br>"]
        PAYLOAD["Payload: <br>•Product name <br>•Brand name <br>•Category <br>• Price <br>•Promo <br>•Ingredients <br>•Link <br>•description"]
        INDEX["Indexes<br>• Price<br>• Category<br>"]
  end
 subgraph subGraph3["Search Engine"]
        SEARCH["Filtering"]
        RANK["Hybrid search"]
  end
 subgraph subGraph4["Explanation Generator"]
        EXPLAIN["Explanation Engine<br>• Ingredient Comparison<br>• Price Analysis<br>"]
  end
 subgraph subGraph5["User Interface Layer"]
        UI["Streamlit Web App"]
        INPUT["Inputs<br>• 2 Images<br>• Text<br>"]
        OUTPUT["Outputs<br>• Alternative Products<br>• Comparisons<br>• Explanations"]
  end
    UI --> INPUT & OUTPUT
    INPUT --> OCR
    EMBED --> QDRANT 
    QDRANT --> VEC2 & PAYLOAD & INDEX & SEARCH
    SEARCH --> RANK
    RANK --> EXPLAIN
    EXPLAIN --> OUTPUT
    OCR --> INGR
    INGR --> EMBED

    style QDRANT fill:#fff4e1
    style SEARCH fill:#e8f5e9
    style EXPLAIN fill:#fce4ec
    style UI fill:#e1f5ff  
```
