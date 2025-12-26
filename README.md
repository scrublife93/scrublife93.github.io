# Sven Adrian - Portfolio & Blog

This repository hosts the personal portfolio website for Sven Adrian, a Zurich-based videographer, and his content hub (currently featuring his "Quest for the Best Burger" blog).

## 💡 Why this Architecture? (Static yet Dynamic)
We built this site using a **"Push" Architecture** to overcome the limitations of **GitHub Pages**:
- **GitHub Pages is Static:** It cannot run a backend server (like Node.js or Python) to fetch data from Notion on-the-fly.
- **Speed:** Fetching data from Notion on every page load would be slow and rate-limited.

**The Solution:**
Instead of a live backend, we use **Python Scripts + GitHub Actions** as a "Build Time" backend.
1. Script fetches data -> 2. Optimizes it -> 3. Bakes it into static JSON/HTML.
The result is a website that loads instantly but still feels dynamic.

---

## 🏗️ Project Structure

### 1. Frontend
- **Placeholders:**
    - **Hero Video:** `index.html` (Lines 167-172) uses a stock video from Mixkit. Replace the `<source>` tag with your own hosted video URL.
    - **Portfolio Grid:** `index.html` (Lines 318-391) contains a hardcoded `const projects = [...]` array to render the video grid.

### 2. The Blog Module (Notion-Powered)
While currently focused on Burgers, this architecture handles any structured content.
- **Source:** Notion Database.
- **Data File:** `assets/data/burgers.json` (Generated).
- **Images:** `assets/images/burgers/` (Synced & Cached).

---

## 🤖 The Automation Pipelines

We rely on two Python scripts to manage content.

### A. The Copywriter (`scripts/enrich_burgers.py`)
*   **Trigger:** Manual (You run it when you want to draft).
*   **Role:** Reads your rough notes and generates professional, SEO-friendly copy.
*   **AI Model:** **Google Gemini 1.5 Flash** (specifically `gemini-3-flash-preview` in code).
*   **Persona:** Defined in the `.env` file under `SEO_PROMPT`. This allows you to adjust the "voice" (e.g., make it more critical, sarcastic, or formal) without touching the code.

### B. The Publisher (`scripts/sync_burgers.py`)
*   **Trigger:** **Daily at 04:00 UTC** (via GitHub Actions) or Manual Dispatch.
*   **Role:** Syncs "Ready to publish" content to the live site.
*   **Key Features:**
    - **Multi-Image Sync:** Downloads all images attached to a burger (`_1.jpg`, `_2.jpg`...).
    - **Signature Caching:** Checks the specific Notion file UUID. If the image hasn't changed, it **skips the download**. This saves bandwidth and keeps builds fast.
    - **Garbage Collection:** Auto-deletes local images that were removed from Notion.

---

## ⚙️ Configuration & Notion

### Environment Variables (.env)
We keep configuration separate from code for security and flexibility.

```bash
# Credentials
NOTION_KEY=secret_...           # Integration Token
NOTION_DATABASE_ID=...          # ID of the Source Database
GEMINI_API_KEY=...             # Google AI Studio Key

# Content Configuration
SEO_PROMPT="You are an expert food critic... Use valid JSON..."
```
*Note: The prompt is here so you can tweak the AI's instructions easily.*

### Required Notion Properties
The scripts are strictly typed. Your Notion Database **MUST** have these exact properties (Case Sensitive):

| Property Name | Type | Key in Code | Description |
| :--- | :--- | :--- | :--- |
| `Name` | Title | `name` | Restaurant Title (e.g., "The Bite"). |
| `Burger Name` | Text | `burgerName` | Specific item (e.g., "Classic Cheese"). |
| `Price (CHF)` | Number | `price` | Cost as a number. |
| `Location` | Multi-select | `place` | e.g., "Zurich". |
| `Last Eaten` | Date | `lastTasted` | Visit date. |
| `Image` | Files & Media | `images` | **Multiple images supported.** |
| `Status` | Status | *(Logic Only)* | Filters: `Improve SEO`, `Ready to publish`. |
| `Review` | Text | `review` | Your raw input notes. |
| `SEO Review` | Text | `seoReview` | **AI Writes to this field.** |
| `SEO Verdict` | Text | `seoVerdict` | **AI Writes to this field.** |
| `Bun` | Number | `ratings.bun` | Rating (1-10). |
| `Patty` | Number | `ratings.meat` | Rating (1-10). |
| `Sauce` | Number | `ratings.sauce` | Rating (1-10). |
| `Value Score` | Number | `valueScore` | Rating (1-10). |
| `Overall Score` | Number | `overallScore` | Rating (1-10). |
| `Value for Money` | Text | `valueForMoney` | e.g. "Steal" or "Pricey". |
| `Certified (Repeated)` | Checkbox | `approved` | Boolean flag. |
| `Short Verdict` | Text | `shortVerdict` | Manual summary (optional). |


---

## 🚀 GitHub Workflows

Defined in `.github/workflows/automate_blog_data.yml`.

| Workflow | Frequency | Action |
| :--- | :--- | :--- |
| **Sync Burgers** | **Daily (04:00 UTC)** | 1. Runs `sync_burgers.py`.<br>2. Checks if `burgers.json` is healthy (not empty).<br>3. Commits changes to the repo.<br>4. Result: Website updates automatically. |
| **Manual Trigger** | On Demand | You can go to `Actions` -> `Automate Blog Data` -> `Run workflow` to force an update immediately. |

---

## 🛠️ Local Development

1.  **Clone & Setup:**
    ```bash
    git clone https://github.com/scrublife93/scrublife93.github.io.git
    cd scrublife93.github.io
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run Sync:**
    ```bash
    python scripts/sync_burgers.py
    ```

3.  **Start Server:**
    ```bash
    python3 -m http.server
    ```
    Visit `http://localhost:8000`.
