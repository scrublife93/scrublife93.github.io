# Sven Adrian - Content Hub & Portfolio

This repository hosts the personal portfolio website for Sven Adrian, a Zurich-based videographer, and his general Content Hub (currently featuring the "Burger Guide" and other articles).

## 💡 Architecture: "Push" vs "Pull"
Accessing Notion directly on every page load is too slow/rate-limited for a high-performance site.
Instead, we use a **Push Architecture**:
1.  **Notion** is the Headless CMS.
2.  **GitHub Actions** act as the "Server" that fetches data.
3.  **Python Scripts** process, optimize, and "bake" the content into static JSON files.
4.  **The Website** reads this static JSON, ensuring instant load times.

---

## 🏗️ Project Components

### 1. Frontend
- **Placeholders:**
    - **Hero Video:** `index.html` (Line 167) uses a stock video. Replace the source with your own hosted file.
    - **Portfolio Data:** `index.html` (Line 318) uses a hardcoded `const projects = [...]` array.
- **Blog Interface:** Renders generic content types (currently specialized for Burgers + Guides).

### 2. The Automation Engine

We have two distinct automated workflows that function as a pipeline.

#### A. The Copywriter (SEO Enrichment)
*   **Workflow:** `.github/workflows/sync_seo.yml`
*   **Trigger:** **Hourly (at minute 13)** OR Manual Dispatch.
*   **Script:** `scripts/enrich_burgers.py`
*   **Role:**
    1.  Scans Notion for pages with status `Improve SEO`.
    2.  Sends the raw notes to **Google Gemini 1.5 Flash** (`gemini-3-flash-preview`).
    3.  Writes a professional "SEO Review" and "SEO Verdict" back to Notion.
    4.  Updates status to `SEO improved`.
*   **Configuration:** The "Persona" (Prompt) is stored in the `.env` file (or GitHub Secrets) as `SEO_PROMPT`. **This ensures your custom writing instructions remain private and are not exposed in the public repo code.**

#### B. The Publisher (Sync to Web)
*   **Workflow:** `.github/workflows/automate_blog_data.yml`
*   **Trigger:** **Daily (04:00 UTC)** OR Manual Dispatch.
*   **Script:** `scripts/sync_burgers.py`
*   **Role:**
    1.  Scans Notion for pages with status `Ready to publish`.
    2.  Downloads content & images to `assets/`.
    3.  **Optimizes Bandwidth:** Uses **Signature-Based Caching** (checking Notion UUIDs) to avoid re-downloading unchanged images.
    4.  Updates `burgers.json`.
    5.  Commits changes and pushes to the repo.
    6.  Updates Notion status to `Published`.

---

## ⚙️ Configuration

### Environment Variables
**Security Note:** We use `.env` (local) and GitHub Secrets (production) to store keys AND Prompts. This prevents sensitive data or proprietary prompting strategies from being leaked in Git history.

```bash
# API Keys
NOTION_KEY=...
NOTION_DATABASE_ID=...
GEMINI_API_KEY=...

# Content Configuration
SEO_PROMPT="You are an expert food critic..." # Kept private
```

### Notion Database Schema
The scripts rely on specific property names. If you change these in Notion, the scripts will break.

| Property Name | Type | Description |
| :--- | :--- | :--- |
| `Name` | Title | Restaurant Name |
| `Status` | Status | Flow: `Draft` -> `Improve SEO` -> `Ready to publish` -> `Published` |
| `Image` | Files & Media | **Supports multiple images.** |
| `Review` | Text | Your raw input. |
| `SEO Review` | Text | **Output target for AI.** |
| `SEO Verdict` | Text | **Output target for AI.** |
| `Burger Name` | Text | |
| `Price (CHF)` | Number | |
| `Location` | Multi-select | |
| `Last Eaten` | Date | |
| `Bun` | Number | Rating |
| `Patty` | Number | Rating |
| `Sauce` | Number | Rating |
| `Value Score` | Number | Rating |
| `Overall Score` | Number | Rating |
| `Value for Money` | Text | |
| `Certified (Repeated)` | Checkbox | |
| `Short Verdict` | Text | Manual summary |

---

## 🛠️ Local Development

1.  **Install:**
    ```bash
    git clone ...
    pip install -r requirements.txt
    ```
2.  **Test AI Copywriter:**
    ```bash
    python scripts/enrich_burgers.py
    ```
3.  **Test Sync/Publish:**
    ```bash
    python scripts/sync_burgers.py
    ```
