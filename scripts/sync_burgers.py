import os
import json
import requests
import shutil
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get and clean env vars
NOTION_KEY = os.getenv("NOTION_KEY", "").strip()
DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "").strip()

if not NOTION_KEY or not DATABASE_ID:
    print("Error: NOTION_KEY or NOTION_DATABASE_ID not set in .env")
    exit(1)

# Ensure ID is dashed
if len(DATABASE_ID) == 32:
    DATABASE_ID = f"{DATABASE_ID[:8]}-{DATABASE_ID[8:12]}-{DATABASE_ID[12:16]}-{DATABASE_ID[16:20]}-{DATABASE_ID[20:]}"

print(f"DEBUG: Using Database ID: {DATABASE_ID}")

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '_', text).strip('_')

def download_image(url, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    path = os.path.join(folder, filename)
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            return path
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
    return None

def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

def update_status_to_published(page_id, burger_name):
    print(f"Publishing burger: {burger_name}...")
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Status": {
                "status": {
                    "name": "Published"
                }
            }
        }
    }
    try:
        response = requests.patch(url, headers=get_notion_headers(), json=payload)
        if response.status_code == 200:
            print(f"Successfully published {burger_name}.")
        else:
            print(f"Failed to publish {burger_name}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception publishing {burger_name}: {e}")

def fetch_burgers():
    print("Fetching burgers from Notion (via requests)...")
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": {
            "or": [
                {
                    "property": "Status",
                    "status": {
                        "equals": "Ready to publish"
                    }
                },
                {
                    "property": "Status",
                    "status": {
                        "equals": "Published"
                    }
                }
            ]
        },
        "sorts": [
            {
                "property": "Overall Score",
                "direction": "descending",
            },
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Error: API Request failed with status {response.status_code}")
            return

        data = response.json()
        results = data.get("results", [])
        print(f"Found {len(results)} pages.")

        burgers = []
        rank_counter = 1
        img_output_dir = "assets/images/burgers" # Relative to project root if run from there
        
        for i, page in enumerate(results):
            props = page["properties"]
            # if i == 0:
            #     print("DEBUG: Value for Money Content:")
            #     print(json.dumps(props.get("Value for Money"), indent=2))
            
            def get_text(prop_name):
                p = props.get(prop_name)
                if not p: return ""
                if p["type"] == "title" and p.get("title"):
                    return p["title"][0]["plain_text"]
                if p["type"] == "rich_text" and p.get("rich_text"):
                    return p["rich_text"][0]["plain_text"]
                if p["type"] == "formula" and p["formula"]["type"] == "string":
                     return p["formula"]["string"] or ""
                return ""

            def get_title(props):
                # Try standard property names for the title
                possible_names = ["Name", "Restaurant", "Burger Place", "Place"]
                for n in possible_names:
                    p = props.get(n)
                    if p and p["type"] == "title" and p.get("title"):
                         return p["title"][0]["plain_text"]
                
                # Fallback: Loop through all properties to find the title
                for key, val in props.items():
                    if val["type"] == "title" and val.get("title"):
                        return val["title"][0]["plain_text"]
                return "Unknown Burger"

            # ... (rest of helpers)

            def get_number(prop_name):
                p = props.get(prop_name)
                if not p: return 0
                if p["type"] == "number":
                    return p["number"] if p.get("number") is not None else 0
                if p["type"] == "formula" and p["formula"]["type"] == "number":
                    return p["formula"]["number"] if p["formula"].get("number") is not None else 0
                return 0

            def get_checkbox(prop_name):
                p = props.get(prop_name)
                return p["checkbox"] if p else False

            def get_date(prop_name):
                p = props.get(prop_name)
                if not p: return ""
                if p["type"] == "date" and p.get("date"):
                     return p["date"]["start"]
                return ""

            def get_multi_select(prop_name):
                p = props.get(prop_name)
                if p and p.get("multi_select") and len(p["multi_select"]) > 0:
                    return p["multi_select"][0]["name"]
                return ""

            def get_status(prop_name):
                p = props.get(prop_name)
                if p and p.get("status"):
                    return p["status"]["name"]
                return ""
            
            name = get_title(props) # Use robust title extractor
            burger_name = get_text("Burger Name")
            base_filename = slugify(name)
            
            local_image_path = "../assets/images/placeholder_burger.jpg"
            
            img_prop = props.get("Image")
            if img_prop and img_prop.get("files") and len(img_prop["files"]) > 0:
                file_obj = img_prop["files"][0]
                img_url = file_obj["file"]["url"] if file_obj["type"] == "file" else file_obj["external"]["url"]
                
                ext = "jpg"
                if "." in img_url.split("?")[0]:
                    ext = img_url.split("?")[0].split(".")[-1]
                if len(ext) > 4: ext = "jpg"

                fname = f"{base_filename}_1.{ext}"
                full_down_path = download_image(img_url, img_output_dir, fname)
                
                if full_down_path:
                    local_image_path = f"../assets/images/burgers/{fname}"

            price_val = get_number("Price (CHF)")
            price_str = f"{price_val:.2f} CHF" if price_val else ""

            status = get_status("Status")
            
            # Check for auto-publish (Handle casing differences)
            if str(status).lower() == "ready to publish":
                update_status_to_published(page["id"], name)
                # No need to update 'status' variable since we don't save it to JSON anymore

            burger = {
                "id": page["id"],
                # "status": status, # Removed as per user request
                "rank": rank_counter,
                "name": name,
                "burgerName": burger_name,
                "price": price_str,
                "place": get_multi_select("Location"),
                "lastTasted": get_date("Last Eaten"),
                "image": local_image_path,
                "ratings": {
                    "bun": get_number("Bun"),
                    "meat": get_number("Patty"),
                    "sauce": get_number("Sauce")
                },
                "review": get_text("Review"),
                "approved": get_checkbox("Certified (Repeated)"),
                "valueScore": get_number("Value Score"),
                "valueForMoney": get_text("Value for Money"),
                "shortVerdict": get_text("Short Verdict"),
                "seoReview": get_text("SEO Review"),
                "seoVerdict": get_text("SEO Verdict"),
                "overallScore": get_number("Overall Score")
            }
            burgers.append(burger)
            rank_counter += 1

        output_path = os.path.join("assets", "data", "burgers.json")
        with open(output_path, "w") as f:
            json.dump(burgers, f, indent=4)
            
        print(f"Successfully synced {len(burgers)} burgers to {output_path}")

    except Exception as e:
        print(f"Error fetching from Notion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_burgers()
