# Sven Adrian - Content Hub & Portfolio

This repository hosts the personal portfolio website for Sven Adrian, a Zurich-based videographer, and his general Content Hub (currently featuring the "Burger Guide" and other articles).

## 💡 Architecture: "Push" vs "Pull"
Accessing Notion directly on every page load is too slow/rate-limited for a high-performance site.
Instead, we use a **Push Architecture**:
1.  **Notion** is the Headless CMS.
2.  **GitHub Actions** act as the "Server" that fetches data.
3.  **Python Scripts** process, optimize, and "bake" the content into static JSON files.
4.  **The Website** reads this static JSON, ensuring instant load times.

This setup bypasses GitHub Pages' lack of dynamic backend support while avoiding the cost/complexity of hosting a full server (like VPS or Heroku). It's "Serverless" in the truest sense.

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
    2.  Sends the raw notes to **Google Gemini 3 Flash** (`gemini-3-flash-preview`).
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
    3.  **Optimizes Bandwidth:** Uses **Signature-Based Caching**.
        *   **Why?** Notion URLs expire and change, but the file content usually doesn't.
        *   **How?** We extract the unique UUID from the Notion URL and store it in `assets/images/burgers/image_manifest.json`.
        *   **Benefit:** The script checks this manifest before downloading. If the signature matches, it skips the download. This saves massive bandwidth and prevents GitHub Actions from hitting network limits.
    4.  Updates `burgers.json` locally.
    5.  *(Note: The Script does NOT commit changes. The GitHub Action handles `git commit` and `git push` after the script finishes).*
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

## ⏱️ Configuring Automation Frequency

You can easily change how often these scripts run by editing the `.github/workflows/` YAML files.

**Example: Change Daily Sync to Weekly**
1.  Open `.github/workflows/automate_blog_data.yml`.
2.  Find the `cron` line:
    ```yaml
    schedule:
      - cron: '0 4 * * *' # Currently: 4:00 AM Daily
    ```
3.  Change it to `0 4 * * 1` (4:00 AM every Monday).
*Tip: Use [crontab.guru](https://crontab.guru) to generate valid cron strings.*

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
4.  **Run Server:**
    ```bash
    python3 -m http.server
    # Open http://localhost:8000 in your browser
    ```

## 🎥 Hero Video Configuration

 The Hero section supports a seamless background video (YouTube) with a high-quality image fallback. By default, the video is **DISABLED** to ensure the site looks perfect until a suitable video is finalized.

 ### How to Enable the Video
 1.  Open `index.html`.
 2.  Search for **`ENABLE_HERO_VIDEO`** in the `<script>` section (near line 200).
 3.  Change `false` to **`true`**.
     ```javascript
     var ENABLE_HERO_VIDEO = true; // Set to TRUE to enable
     ```

 ### How to Change the Video
 To use your own video, find the `initPlayer()` function in `index.html` and update the **`videoId`**:
 ```javascript
 player = new YT.Player('hero-player', {
     videoId: 'YOUR_YOUTUBE_ID_HERE', // e.g., '5t_jbUukQwc'
     // ...
 });
 ```

 ### Configuration Options
 | Variable | Description | Default |
 | :--- | :--- | :--- |
 | `ENABLE_HERO_VIDEO` | Master switch. If `false`, site uses static image only. | `false` |
 | `TRANSITION_DELAY_MS` | Delay (ms) before fading out the poster image after video starts. Increase this if you see buffering artifacts. | `1000` |
 | **Mobile Behavior** | The video is **programmatically disabled** on screens smaller than 768px to save bandwidth, regardless of the `ENABLE` flag. | N/A |

## Image Optimization
The sync script automatically optimizes images download from Notion:
- Converts to **WebP** format.
- Resizes to a maximum dimension (default 1600px).
- Respects EXIF orientation.

### Adjusting Quality & Size
To change the image settings, edit the constants at the top of `scripts/sync_burgers.py`:
```python
# Image Configuration
IMAGE_QUALITY = 90       # WebP Quality (0-100)
IMAGE_MAX_SIZE = 1600    # Max width/height in pixels
```
