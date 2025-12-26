import os
import json
import requests
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_KEY = os.getenv("NOTION_KEY", "").strip()
DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not NOTION_KEY or not DATABASE_ID:
    print("Error: NOTION_KEY or NOTION_DATABASE_ID not set in .env")
    exit(1)

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set in .env")
    exit(1)

# Configure Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3-flash-preview" 

# Ensure ID is dashed
if len(DATABASE_ID) == 32:
    DATABASE_ID = f"{DATABASE_ID[:8]}-{DATABASE_ID[8:12]}-{DATABASE_ID[12:16]}-{DATABASE_ID[16:20]}-{DATABASE_ID[20:]}"

def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

def fetch_burgers_for_enrichment():
    print("Fetching burgers with status 'Improve SEO'...")
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    payload = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "Improve SEO"
            }
        }
    }

    try:
        response = requests.post(url, headers=get_notion_headers(), json=payload)
        if response.status_code != 200:
            print(f"Error fetching: {response.status_code} - {response.text}")
            return []
        
        return response.json().get("results", [])
    except Exception as e:
        print(f"Exception fetching: {e}")
        return []

def update_notion_page(page_id, seo_review, seo_verdict):
    print(f"Updating page {page_id}...")
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    payload = {
        "properties": {
            "SEO Review": {
                "rich_text": [
                    {
                        "text": {
                            "content": seo_review
                        }
                    }
                ]
            },
            "SEO Verdict": {
                "rich_text": [
                    {
                        "text": {
                            "content": seo_verdict
                        }
                    }
                ]
            },
            "Status": {
                "status": {
                    "name": "SEO improved"
                }
            }
        }
    }
    
    try:
        response = requests.patch(url, headers=get_notion_headers(), json=payload)
        if response.status_code == 200:
            print("Successfully updated Notion.")
        else:
            print(f"Failed to update Notion: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception updating: {e}")

def generate_seo_content(burger_data):
    # Debug: Print keys to see why Name might be missing
    # print(f"DEBUG: Data keys: {list(burger_data.keys())}")
    
    burger_name = burger_data.get('Name') or burger_data.get('Burger Name') or "Unknown Burger"
    print(f"Generating SEO content for: {burger_name}...")
    
    # Format data nicely for the prompt to avoid sending raw JSON with unwanted fields
    # Exclude: Value Score, Last Eaten
    
    # Handle Location list safely
    loc = burger_data.get('Location', ['Unknown'])
    location_str = loc[0] if isinstance(loc, list) and len(loc) > 0 else "Unknown"

    review_context = f"""
    Restaurant: {burger_data.get('Restaurant Name') or burger_data.get('Name', 'Unknown')}
    Burger: {burger_data.get('Burger Name', 'Unknown')}
    Location: {location_str}
    Price: {burger_data.get('Price (CHF)', 'N/A')} CHF
    Value for Money: {burger_data.get('Value for Money', 'N/A')}
    
    Overall Score: {burger_data.get('Overall Score', 'N/A')}/10
    
    Ratings:
    - Bun: {burger_data.get('Bun', 'N/A')}/10
    - Meat: {burger_data.get('Patty', 'N/A')}/10
    - Sauce: {burger_data.get('Sauce', 'N/A')}/10
    
    Original Review: 
    "{burger_data.get('Review', '')}"
    
    Short Verdict (Existing): "{burger_data.get('Short Verdict', '')}"
    """
    print(review_context)
    try:
        prompt = f"""
        You are an expert food critic and SEO specialist.
        I have a burger review that needs improved copy for a blog.
        
        Review Data:
        {review_context}
        
        Task:
        1. Rewrite the "Review" text to be engaging and SEO-friendly.
           - STRICT CONSTRAINT: Do NOT include ANY numerical scores (e.g. "10/10", "5 stars") or prices.
           - Tone: Authentic, critical but fair. Avoid "hype" words like "world-class" unless truly warranted by a perfect score.
        2. Create a "Short Verdict": a punchy, one-sentence summary.
           - STRICT CONSTRAINT: Must be UNDER 12 WORDS.
           - NO numbers or prices in the verdict.
        
        Return ONLY valid JSON with no extra text or markdown formatting:
        {{
            "seo_review": "...",
            "seo_verdict": "..."
        }}
        """
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        
        # New SDK returns object, usually we access .text or .parsed
        # If we use response_mime_type json, we might get it directly?
        # Let's rely on .text and json.loads for safety as per documentation patterns
        if response.text:
             return json.loads(response.text)
        return None
        
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

def process_burgers():
    pages = fetch_burgers_for_enrichment()
    print(f"Found {len(pages)} burgers to process.")
    
    for page in pages:
        props = page["properties"]
        
        # NOTE: We no longer check if fields are empty.
        # If status is "Improve SEO", we treat it as a request to generate/overwrite content.
            
        # Extract Data for AI
        def get_plain_text(p):
            if not p: return ""
            if p["type"] == "rich_text": return p["rich_text"][0]["plain_text"] if p["rich_text"] else ""
            if p["type"] == "title": return p["title"][0]["plain_text"] if p["title"] else ""
            return ""

        data_for_ai = {}
        for key, value in props.items():
            if key in ["Status", "SEO Review", "SEO Verdict"]:
                continue
            
            # Simple extraction of values for context
            if value["type"] == "number":
                data_for_ai[key] = value["number"]
            elif value["type"] in ["title", "rich_text"]:
                data_for_ai[key] = get_plain_text(value)
            elif value["type"] == "select":
                data_for_ai[key] = value["select"]["name"] if value["select"] else ""
            elif value["type"] == "multi_select":
                data_for_ai[key] = [o["name"] for o in value["multi_select"]]
            elif value["type"] == "date":
                data_for_ai[key] = value["date"]["start"] if value["date"] else ""
            elif value["type"] == "checkbox":
                data_for_ai[key] = value["checkbox"]
            elif value["type"] == "formula":
                if value["formula"]["type"] == "string":
                     data_for_ai[key] = value["formula"]["string"]
                elif value["formula"]["type"] == "number":
                     data_for_ai[key] = value["formula"]["number"]

        # Generate
        result = generate_seo_content(data_for_ai)
        
        if result:
            update_notion_page(page["id"], result["seo_review"], result["seo_verdict"])

if __name__ == "__main__":
    process_burgers()
