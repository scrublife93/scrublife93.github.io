# Sven Adrian - Portfolio & Burger Blog

This repository hosts the personal portfolio website for Sven Adrian, a Zurich-based videographer, and his "Quest for the Best Burger" blog.

The site is a hybrid **Static + Dynamic** architecture:
- **Frontend:** Pure HTML, TailwindCSS (for styling), and Vanilla JS.
- **Backend/CMS:** **Notion** acts as the Headless CMS.
- **Automation:** Python scripts + GitHub Actions handle data syncing, image optimization, and AI content enrichment.

---

## 🏗️ Project Architecture

### 1. Frontend (`index.html` & `blog/`)
The site is divided into two main sections:
- **Portfolio (Home):** A single-page cinematic showcase of video work.
    - **Placeholders:**
        - **Hero Video:** Currently uses a stock video from Mixkit (Lines 167-172 in `index.html`). *To replace: update the `src` attribute.*
        - **Projects Grid:** The video portfolio data (`const projects = [...]`) is currently **hardcoded** in `index.html` (Lines 318-391).
- **Burger Blog:** A simplified static rendering of the burger reviews fetched from Notion.
    - Data source: `assets/data/burgers.json` (Generated automatically).

### 2. The Automation Engine (How it works)
We use a "Push" architecture. Instead of the website fetching data from Notion on every load (slow), we run scripts to fetch, process, and "bake" the data into JSON files. This ensures the site is blazing fast.

#### 🔄 The Workflow
1.  **Drafting:** You add a new burger review in Notion with status `Improve SEO`.
2.  **AI Enrichment:** The `enrich_burgers.py` script runs (locally or via dispatch). It uses **Google Gemini 2.0** to read your raw review and write a polished "SEO Review" and "SEO Verdict" back to Notion. Status updates to `SEO improved`.
3.  **Review:** You check the AI's work in Notion. If satisfied, change status to `Ready to publish`.
4.  **Publishing:** The `sync_burgers.py` script runs (Auto-daily or Manual). It:
    - Downloads the burger data.
    - Downloads & Optimizes images (with caching).
    - Updates `burgers.json`.
    - Updates Notion status to `Published`.
    - commits changes to the repo.

---

## 🤖 The Scripts

### `scripts/enrich_burgers.py` (The AI Copywriter)
*   **Trigger:** Manual run or GitHub Action dispatch.
*   **Role:** Takes raw notes and turns them into professional copy.
*   **Model:** `gemini-3-flash-preview` (Fast & High Quality).
*   **Prompting:** The system prompt is defined in `.env` (or defaults in script) to maintain a specific "Food Critic" persona.

### `scripts/sync_burgers.py` (The Publisher)
*   **Trigger:** Daily (04:00 UTC) via GitHub Actions.
*   **Role:** Syncs content from Notion to the Website.
*   **Key Features:**
    - **Multi-Image Support:** Downloads all images attached to a burger (`_1.jpg`, `_2.jpg`...).
    - **Signature Caching:** Checks the specific Notion file UUID. If the image hasn't changed, it **skips downloading** to save bandwidth and speed up builds.
    - **Garbage Collection:** Automatically deletes local images (`assets/images/burgers/`) that are no longer in Notion, keeping the repo clean.

---

## ⚙️ Configuration & Adjustments

### Environment Variables
This project relies on a `.env` file for local development (and GitHub Secrets for production).

```bash
NOTION_KEY=secret_...           # Your Notion Integration Token
NOTION_DATABASE_ID=...          # The ID of your Burger Database
GEMINI_API_KEY=...             # Google AI Studio Key for Enrichment
```

### Notion Database Setup
 The scripts expect specific properties in your Notion Database. If you rename these in Notion, you **MUST** update `sync_burgers.py`:

| Property Name | Type | Description |
| :--- | :--- | :--- |
| `Name` | Title | The restaurant name. |
| `Burger Name` | Text | Specific item ordered. |
| `Price (CHF)` | Number | Price in Swiss Francs. |
| `Location` | Multi-select | City/Area (e.g., Zurich). |
| `Last Eaten` | Date | Visit date. |
| `Image` | Files & Media | Upload your photos here. |
| `Status` | Status | Lifecycle: `Draft` -> `Improve SEO` -> `Ready` -> `Published`. |
| `Review` | Text | Your raw notes. |
| `SEO Review` | Text | **AI Generated** output. |

### How to...

#### ...Replace the Hero Video?
1.  Upload your video to `assets/images/` (or host it externally).
2.  Open `index.html`.
3.  Find line 170 (`<source src="...">`) and update the path.

#### ...Add a new Rating Category?
1.  **Notion:** Add the new Number property (e.g., "Fries").
2.  **`sync_burgers.py`:** Add a helper function `fries = get_number("Fries")` inside the loop and add it to the `burger` dictionary.
3.  **Frontend:** Update your JS to display the new rating from the JSON.

#### ...Change the AI Behavior?
1.  Open `scripts/enrich_burgers.py`.
2.  Locate the `generate_seo_content` function.
3.  Edit the `prompt` string to change the tone (e.g., "Be more sarcastic" or "Focus on texture").

---

## 🚀 Deployment (GitHub Actions)
The workflow is defined in `.github/workflows/automate_blog_data.yml`.

- **Schedule:** Runs automatically every day at 4 AM UTC.
- **Manual Trigger:** Go to Actions -> Select Workflow -> "Run workflow".
- **Safety:** It verifies data integrity before committing and only touches the `assets/` folder.

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
