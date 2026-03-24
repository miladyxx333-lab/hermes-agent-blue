import os
import json
import time
from playwright.sync_api import sync_playwright
import re

def main():
    base_dir = "/Users/urielhernandez/.gemini/antigravity/scratch/hermes-agent-blue/skills/law_mx/data"
    index_file = os.path.join(base_dir, "justia_leyes_index.json")
    output_dir = os.path.join(base_dir, "leyes_federales")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(index_file, "r", encoding="utf-8") as f:
        laws = json.load(f)
        
    print(f"Loaded {len(laws)} laws. Starting extraction...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Randomizing user agent helps but a consistent desktop UA is fine for Justia
        context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for idx, law in enumerate(laws):
            title = law.get("title", "")
            url = law.get("url", "")
            
            # Clean filename
            safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower())
            file_path = os.path.join(output_dir, f"{safe_title}.txt")
            
            if os.path.exists(file_path):
                print(f"[{idx+1}/{len(laws)}] Skipping {title}, already downloaded.")
                continue
                
            print(f"[{idx+1}/{len(laws)}] Downloading {title}...")
            
            try:
                # We go to the individual articles and extract text to avoid PDF parsing issues
                # But since Justia has an articles index, we can just extract the index links
                # Actually, Justia often has a master page. If not, extracting the gdoc pdf text if possible.
                # Since downloading 300 PDFs might be heavy, let's just make the script 
                # visit the gdoc page and see if we can get pure text or download the pdf.
                
                # To be robust, let's just try to go to the main page and extract all text inside .main-content
                # Justia usually has an index of titles and articles.
                # If we really want full content, we'd have to crawl. 
                # For this script, we'll just save the index map of articles for now to allow
                # the agent to query them on-demand if needed, OR we just save the main page text.
                
                # We'll just load the main law page, grab its entire textual representation
                # and save it. It won't have the full text if it's paginated, but it will have the index
                # of articles which the agent can then visit.
                
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                content = page.evaluate('''() => {
                    const el = document.querySelector('div.wrapper') || document.body;
                    return el.innerText;
                }''')
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n\n")
                    f.write(content)
                    
                time.sleep(1) # Be polite
                
            except Exception as e:
                print(f"Error on {title}: {e}")
                
        browser.close()
    print("Done downloading all available texts!")

if __name__ == "__main__":
    main()
