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

final_prompt = """
You are comparing a reference product to similar alternatives found via vector search. 

**REFERENCE PRODUCT:**
- Name: {product_name}
- Key Ingredients (in order of importance): {ingredients}

**ALTERNATIVES:**
{alternatives}

**TASK:** For each alternative, create an HTML comparison card explaining:
1. **Overall Similarity Score** (0-100%) - semantic + ingredient overlap
2. **Ingredient Match Breakdown** - which ingredients match, position similarity  
3. **Price/Category Confirmation** - budget fit + category match
4. **Product Link** - clickable "View Product" button with the URL
5. **Why This Is A Good Alternative** - clear reasoning

**OUTPUT REQUIREMENTS:**
- Return ONLY valid HTML (no markdown, no code blocks)
- Beautiful gradient cards (modern design)
- Green highlights for ✅ matches, orange ⚠️ for partial, red ❌ for missing
- **MUST include clickable link button** for each product using the URL provided
- Top 3-5 alternatives only
- Professional, scannable layout for e-commerce app

**EXAMPLE HTML STRUCTURE:**
<div style='display: flex; flex-direction: column; gap: 1.5rem;'>
  <div style='background: linear-gradient(135deg, #4ade80, #22c55e); color: white; padding: 1.5rem; border-radius: 15px;'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
      <h3>🥇 Alternative #1 - Brand Product (12.99dt)</h3>
      <span style='font-size: 1.3rem; font-weight: bold;'>95%</span>
    </div>
    <div style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
      <p><strong>✅ Ingredients Match (9/10):</strong> nuts, milk, sugar <span style='color: #86efac'>✓ same positions</span></p>
      <p><strong>✅ Price:</strong> Under budget | <strong>✅ Category:</strong> Shampoo</p>
      <p><em>Excellent match - identical top 3 ingredients in same order</em></p>
      <a href="https://example.com/product" target="_blank" 
         style='display: inline-block; margin-top: 1rem; padding: 0.75rem 1.5rem; 
                background: white; color: #22c55e; border-radius: 8px; 
                text-decoration: none; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        🛒 View Product
      </a>
    </div>
  </div>
</div>
"""

def get_alternatives_html(product_name, ingredients, category, budget):
    """Generate HTML for alternatives using Groq"""
    client = get_groq_client()
    
    # Get alternatives from Qdrant
    alternatives = get_alternatives(
        ingredients=ingredients,
        category=category,
        budget=budget
    )
    
    # Check if we got results
    if not alternatives:
        return """
        <div style='background: linear-gradient(135deg, #fbbf24, #f59e0b); 
                   padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
            <h3>⚠️ No alternatives found</h3>
            <p>Try adjusting your budget or check if the category is correct.</p>
        </div>
        """
    
    # Format alternatives for prompt
    alternatives_text = ""
    for i, alt in enumerate(alternatives[:5], 1):
        payload = alt.payload
        score = alt.score if hasattr(alt, 'score') else 0
        alternatives_text += f"""
Alternative {i}:
- Name: {payload.get('product_name', 'Unknown')}
- Brand: {payload.get('product_brand', 'Unknown')}
- Price: {payload.get('price', 0):.2f}dt
- URL: {payload.get('url', 'Not available')}
- Similarity Score: {score:.3f}
- Ingredients: {payload.get('ingredients', 'Not available')[:200]}...

"""
    
    # Generate HTML for alternatives
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates beautiful HTML for product comparisons."},
                {"role": "user", "content": final_prompt.format(
                    product_name=product_name,
                    ingredients=", ".join(ingredients[:10]),
                    alternatives=alternatives_text
                )}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating alternatives HTML: {e}")
        return f"<p>Error: {str(e)}</p>"


# Helper function to parse ingredients (✅ FIXED: use semicolon)
def parse_ingredients_list(ingredients_text):
    """Extract clean list of ingredients from AI response"""
    # Remove any markdown, extra text
    ingredients_text = ingredients_text.strip()
    
    # Split by semicolon (as requested in prompt)
    if ';' in ingredients_text:
        ingredients = [ing.strip() for ing in ingredients_text.split(';') if ing.strip()]
    else:
        # Fallback: try comma if semicolon not found
        ingredients = [ing.strip() for ing in ingredients_text.split(',') if ing.strip()]
    
    # Clean up - remove any "Format:" or instruction text
    ingredients = [ing for ing in ingredients if not ing.lower().startswith(('format', 'ingredient'))]
    
    # Lowercase for matching
    ingredients = [ing.lower() for ing in ingredients]
    
    return ingredients[:20]  # Top 20 ingredients


# Streamlit UI
def main():
    st.set_page_config(page_title="Product Information Extractor", layout="wide")
    
    st.title("🛍️ ParaSave: Wellnes Product Information Extractor & Alternatives Finder")
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
            "Max budget per alternative (dt)",
            min_value=0.000,
            value=10.000,
            step=0.100,
            format="%.2f"
        )
        st.metric("🔎 Searching alternatives under", f"{budget:.2f}dt")
    
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
                
                # Display extracted info for debugging
                with st.expander("🔍 Extracted Information (Debug)"):
                    st.write("**Product Info:**", product_info)
                    st.write("**Category:**", category)
                    st.write("**Raw Ingredients:**", ingredients_list)
                
                # Parse ingredients
                ingredients_clean = parse_ingredients_list(ingredients_list)
                
                st.write("**Parsed Ingredients:**", ingredients_clean)
                
                # Validate category
                valid_categories = ["solar", "foodSup", "faceGel"]
                if category not in valid_categories:
                    st.error(f"⚠️ Invalid category: {category}. Must be one of: {valid_categories}")
                    st.stop()
                
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
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;'>
                    <h2 style='margin: 0 0 1rem 0;'>📦 Original Product</h2>
                    <div style='font-size: 1.1rem; line-height: 1.6;'>
                        <strong>Name:</strong> {product_info}<br>
                        <strong>Category:</strong> {category}<br>
                        <strong>Budget:</strong> {budget:.2f}dt<br>
                        <strong>Key Ingredients:</strong> {", ".join(ingredients_clean[:5])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Alternatives Results
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;'>
                    <h3 style='margin: 0;'>🔄 Budget-Friendly Alternatives</h3>
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

if __name__ == "__main__":
    main()