import streamlit as st
import base64
from groq import Groq
import os
from PIL import Image
import io
from dotenv import load_dotenv

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

# Streamlit UI
def main():
    st.set_page_config(page_title="Product Information Extractor", layout="wide")
    
    st.title("🛍️ Product Information Extractor")
    st.markdown("Extract product details and ingredients from images using Groq Vision AI")
    
    # Initialize Groq client
    client = get_groq_client()
    
    # Create three columns for inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Product Image")
        product_image = st.file_uploader(
            "Upload product image (shows name & brand)",
            type=['png', 'jpg', 'jpeg'],
            key="product"
        )
        if product_image:
            st.image(product_image, caption="Product Image", use_container_width=True)
    
    with col2:
        st.subheader("Ingredients Image")
        ingredients_image = st.file_uploader(
            "Upload ingredients/description image",
            type=['png', 'jpg', 'jpeg'],
            key="ingredients"
        )
        if ingredients_image:
            st.image(ingredients_image, caption="Ingredients Image", use_container_width=True)
    
    with col3:
        st.subheader("Budget")
        budget = st.number_input(
            "Enter budget amount",
            min_value=0.000,
            value=0.000,
            step=0.001,
            format="%.3f"
        )
        st.metric("Current Budget", f"${budget:.3f}")
    
    # Process button
    st.markdown("---")
    
    if st.button("🔍 Extract Information", type="primary", use_container_width=True):
        if not product_image or not ingredients_image:
            st.warning("⚠️ Please upload both images before extracting information.")
        else:
            with st.spinner("Analyzing images with Groq Vision AI..."):
                # Encode images
                product_b64 = encode_image(product_image)
                ingredients_b64 = encode_image(ingredients_image)
                
                # Create results columns
                result_col1, result_col2 = st.columns(2)
                
                with result_col1:
                    st.subheader("📦 Product Information")
                    with st.spinner("Extracting product name and brand..."):
                        product_info = extract_product_info(client, product_b64)
                        st.markdown(product_info)
                    
                    st.subheader("🏷️ Product Category")
                    with st.spinner("Identifying category..."):
                        category = extract_category(client, product_b64)
                        if "not one of the categories" in category.lower():
                            st.warning(f"⚠️ {category}")
                        else:
                            st.success(f"**Category:** {category}")
                
                with result_col2:
                    st.subheader("🧪 Ingredients/Composition")
                    with st.spinner("Extracting ingredients..."):
                        ingredients_info = extract_ingredients(client, ingredients_b64)
                        st.markdown(ingredients_info)
                
                # Display budget info
                st.markdown("---")
                st.info(f"💰 Budget allocated for this product: ${budget:.3f}")
                
                # Summary section
                st.subheader("📋 Summary")
                summary_data = {
                    "Budget": f"${budget:.3f}",
                    "Category": category,
                    "Product Analysis": "Completed ✅",
                    "Ingredients Analysis": "Completed ✅"
                }
                
                for key, value in summary_data.items():
                    st.write(f"**{key}:** {value}")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Powered by Groq Vision AI | Multilingual Support Enabled</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()