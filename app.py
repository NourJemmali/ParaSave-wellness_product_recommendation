from urllib import response
import streamlit as st
import base64
from groq import Groq
import os
from PIL import Image
import io
from dotenv import load_dotenv
from utils import get_alternatives
# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("Please set GROQ_API_KEY environment variable")
        st.stop()
    return Groq(api_key=api_key)

# Function to encode image to base64
def encode_image(image_file):
    """Convert uploaded image to base64 string"""
    if image_file is not None:
        bytes_data = image_file.getvalue()
        return base64.b64encode(bytes_data).decode('utf-8')
    return None

# Function to extract product name and brand
def extract_product_info(client, image_base64):
    """Extract product name and brand from image using Groq VLM"""
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this product image and extract the following information:

Please provide the information in this exact format:
Product Name: [name]
Provide the whole name not just the brand
If the text is in a language other than English, please provide the original text."""
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract ingredients/composition
def extract_ingredients(client, image_base64):
    """Extract ingredients/composition from image using Groq VLM"""
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this image and extract all ingredients or composition information visible.

Please list all ingredients/components you can identify, maintaining the original language if it's not in English.

IMPORTANT: Return the ingredients as a single line separated by semicolons (;)

Format:
ingredient1;ingredient2;ingredient3;ingredient4

If percentages or quantities are mentioned, include them with the ingredient name."""
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract product category
def extract_category(client, image_base64):
    """Extract product category from predefined categories using Groq VLM"""
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this product image and determine which category it belongs to.

The ONLY valid categories are:
1. solar - Solar cream, sun cream, crème solaire, écran solaire
2. foodSup - Food supplements, vitamins, dietary supplements, complément alimentaire
3. faceGel - Face gels, gel nettoyant, purifiant, clean

Instructions:
- Respond with ONLY ONE of these exact words: solar, foodSup, or faceGel
- If the product does not fit ANY of these categories, respond with: "Not one of the categories we are dealing with"
- Be strict: only choose a category if you are confident the product fits

Your response:"""
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"
final_prompt=
"""
You are comparing a reference product to similar alternatives found via vector search. 

**REFERENCE PRODUCT:**
- Name: {product_name}
- Key Ingredients (in order of importance): {ingredients}

**ALTERNATIVES** :
{alternatives}

**TASK:** For each alternative, create an HTML comparison card explaining:
1. **Overall Similarity Score** (0-100%) - semantic + ingredient overlap
2. **Ingredient Match Breakdown** - which ingredients match, position similarity  
3. **Price/Category Confirmation** - budget fit + category match
4. **Why This Is A Good Alternative** - clear reasoning

**OUTPUT REQUIREMENTS:**
- Return ONLY valid HTML (no markdown, no code blocks)
- Beautiful gradient cards (modern design)
- Green highlights for ✅ matches, orange ⚠️ for partial, red ❌ for missing
- Top 3-5 alternatives only
- Professional, scannable layout for e-commerce app

**EXAMPLE HTML STRUCTURE:**
html
<div style='display: flex; flex-direction: column; gap: 1.5rem;'>
  <div style='background: linear-gradient(135deg, #4ade80, #22c55e); color: white; padding: 1.5rem; border-radius: 15px;'>
    <div style='display: flex; justify-content: space-between;'>
      <h3>🥇 Alternative #1 - Brand Product ($12.99)</h3>
      <span style='font-size: 1.3rem; font-weight: bold;'>95%</span>
    </div>
    <div style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
      <p><strong>✅ Ingredients Match (9/10):</strong> nuts, milk, sugar <span style='color: #86efac'>✓ same positions</span></p>
      <p><strong>✅ Price:</strong> Under budget | <strong>✅ Category:</strong> Shampoo</p>
      <p><em>Excellent match - identical top 3 ingredients in same order</em></p>
    </div>
  </div>
</div>"""
def get_alternatives_html(product_name, ingredients, category, budget):
    client = get_groq_client()
    alternatives= get_alternatives(
        ingredients=ingredients,
        category=category,
        budget=budget)
    # Generate HTML for alternatives
    response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_prompt.format(
                product_name=product_name,
                ingredients=", ".join(ingredients),
                category=category,
                budget=budget
            )}
            ],
            temperature=0.1,
            max_tokens=1000
        )

    return response.choices[0].message.content
# Streamlit UI
def main():
    st.set_page_config(page_title="Product Information Extractor", layout="wide")
    
    st.title("🛍️ Product Information Extractor & Alternatives Finder")
    st.markdown("Extract product details and find **budget-friendly alternatives** using AI-powered search")
    
    # Initialize Groq client
    client = get_groq_client()
    
    # Create three columns for inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📦 Product Image")
        product_image = st.file_uploader(
            "Upload product image", 
            type=['png', 'jpg', 'jpeg'],
            key="product"
        )
        if product_image:
            st.image(product_image, caption="Product Image", use_container_width=True)
    
    with col2:
        st.subheader("🧪 Ingredients Image")
        ingredients_image = st.file_uploader(
            "Upload ingredients list", 
            type=['png', 'jpg', 'jpeg'],
            key="ingredients"
        )
        if ingredients_image:
            st.image(ingredients_image, caption="Ingredients Image", use_container_width=True)
    
    with col3:
        st.subheader("💰 Budget")
        budget = st.number_input(
            "Max budget per alternative ($)",
            min_value=0.000,
            value=10.000,
            step=0.100,
            format="%.2f"
        )
        st.metric("🔎 Searching alternatives under", f"${budget:.2f}")
    
    # Process button
    st.markdown("---")
    
    if st.button("🚀 Extract & Find Alternatives", type="primary", use_container_width=True):
        if not product_image or not ingredients_image:
            st.warning("⚠️ Please upload **both images** and set your budget!")
        else:
            with st.spinner("🔍 Analyzing images + searching alternatives..."):
                # Encode images
                product_b64 = encode_image(product_image)
                ingredients_b64 = encode_image(ingredients_image)
                
                # Extract information
                with st.spinner("Extracting product details..."):
                    product_info = extract_product_info(client, product_b64)
                    category = extract_category(client, product_b64)
                    ingredients_list = extract_ingredients(client, ingredients_b64)
                
                # Extract clean ingredients list (you may need to parse this)
                ingredients_clean = parse_ingredients_list(ingredients_list)  # Your parsing func
                
                # CALL get_alternatives FUNCTION
                st.info("🎯 Finding similar alternatives...")
                alternatives_html = get_alternatives_html(
                    product_name=product_info,
                    ingredients=ingredients_clean,
                    category=category,
                    budget=budget
                )
                
                # BEAUTIFUL RESULTS DISPLAY
                st.markdown("## 🎉 **Results**")
                
                # Product Summary Card
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;'>
                    <h2 style='margin: 0 0 1rem 0;'>📦 **Original Product**</h2>
                    <div style='font-size: 1.1rem; line-height: 1.6;'>
                        <strong>Category:</strong> """ + category + """<br>
                        <strong>Budget:</strong> $""" + str(budget) + """<br>
                        <strong>Key Ingredients:</strong> """ + ", ".join(ingredients_clean[:5]) + """
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Alternatives Results
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;'>
                    <h3 style='margin: 0;'>🔄 **Budget-Friendly Alternatives**</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # RENDER ALTERNATIVES HTML
                st.markdown(alternatives_html, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
        <h4>✨ Powered by Groq Vision AI + Qdrant Vector Search</h4>
        <p><em>Find the best alternatives within your budget instantly!</em></p>
    </div>
    """, unsafe_allow_html=True)

# Helper function to parse ingredients (adjust as needed)
def parse_ingredients_list(ingredients_text):
    """Extract clean list of ingredients from AI response"""
    # Simple parsing - replace with your actual logic
    ingredients = [ing.strip() for ing in ingredients_text.split(',') if ing.strip()]
    return ingredients[:10]  # Top 10 ingredients

if __name__ == "__main__":
    main()