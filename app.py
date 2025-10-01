import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # columns: title, authors, genres, image_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Lowercased helper columns
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Pagination settings
POPULAR_PAGE_SIZE = 20
RANDOM_SAMPLE_SIZE = 12  # Number of random books to show

def get_random_books(n=RANDOM_SAMPLE_SIZE, query=""):
    """Get random sample of books, filtered by query if provided"""
    if query:
        query = query.strip().lower()
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
        
        if len(filtered) == 0:
            return filtered
        elif len(filtered) <= n:
            return filtered
        else:
            return filtered.sample(n=n, random_state=42)
    else:
        # No query - return true random sample
        if len(df) <= n:
            return df
        return df.sample(n=n, random_state=42)

def get_popular_books(page=0):
    """Get paginated popular books (unaffected by search)"""
    # Show popular books (first N books, or you could sort by rating if available)
    filtered = df
    
    # Pagination
    start = page * POPULAR_PAGE_SIZE
    end = start + POPULAR_PAGE_SIZE
    page_data = filtered.iloc[start:end]

    # Prepare gallery data
    gallery_data = []
    for _, row in page_data.iterrows():
        img = row["image_url"]
        title = row["title"]
        authors = ", ".join(row["authors"])
        genres = ", ".join(row["genres"][:3])  # Show max 3 genres
        
        caption = f"**{title}**\nby {authors}\n*{genres}*"
        gallery_data.append((img, caption))
    
    # Return gallery + next page availability
    has_next = end < len(filtered)
    total_results = len(filtered)
    
    return gallery_data, has_next, total_results

def prepare_gallery_data(dataframe):
    """Convert dataframe to gallery format"""
    gallery_data = []
    for _, row in dataframe.iterrows():
        img = row["image_url"]
        title = row["title"]
        authors = ", ".join(row["authors"])
        genres = ", ".join(row["genres"][:3])
        
        caption = f"**{title}**\nby {authors}\n*{genres}*"
        gallery_data.append((img, caption))
    return gallery_data

# Initial load - show random books and popular books
def initial_load(query=""):
    # Random books (affected by search)
    random_books = get_random_books(query=query)
    random_gallery = prepare_gallery_data(random_books)
    
    # Popular books (UNAFFECTED by search)
    popular_gallery, has_next, total_results = get_popular_books(page=0)
    
    if query:
        results_text = f"🎲 Found {len(random_books)} random books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_gallery, popular_gallery, 0, gr.update(visible=has_next), results_text

# Load more functionality for popular books
def load_more(page, current_popular_gallery):
    page += 1
    gallery_data, has_next, total_results = get_popular_books(page)
    # Append new results to existing gallery
    new_gallery = current_popular_gallery + gallery_data
    return new_gallery, page, gr.update(visible=has_next)

# Refresh random books (with current search if any)
def refresh_random(query):
    random_books = get_random_books(query=query)
    random_gallery = prepare_gallery_data(random_books)
    
    if query:
        results_text = f"🎲 Found {len(random_books)} random books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_gallery, results_text

# Clear search - resets to default view
def clear_search():
    return "", *initial_load("")

# Build UI with two sections
with gr.Blocks(css="""
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
    }
    .scroll-horizontal {
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 15px 5px;
        min-height: 280px;
    }
    .scroll-horizontal .thumbnail {
        flex: 0 0 auto;
        width: 160px;
        height: 240px;
        object-fit: cover;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .scroll-horizontal .thumbnail:hover {
        transform: scale(1.05);
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding: 0 10px;
    }
    .section-title {
        font-size: 1.3em;
        font-weight: bold;
        color: #333;
        margin: 0;
    }
    .results-info {
        font-size: 14px;
        color: #666;
        margin: 10px 0;
        font-weight: bold;
        padding: 0 10px;
    }
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
    }
    .refresh-btn {
        background: #4CAF50;
        color: white;
        border: none;
    }
    .load-more-container {
        display: flex;
        justify-content: center;
        margin-top: 15px;
    }
    /* Custom scrollbar */
    .scroll-horizontal::-webkit-scrollbar {
        height: 8px;
    }
    .scroll-horizontal::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .scroll-horizontal::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    .scroll-horizontal::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
""") as demo:
    
    with gr.Column():
        # Header
        with gr.Row():
            with gr.Column():
                gr.Markdown("""
                # 📚 Book Explorer
                *Discover your next favorite read*
                """, elem_classes="search-header")
        
        # Search Section
        with gr.Row():
            search_box = gr.Textbox(
                label="",
                placeholder="🔍 Search random books by title, author, or genre...",
                value="",
                scale=4
            )
            clear_btn = gr.Button("Clear Search", scale=1, variant="secondary")
        
        # Random Books Section (affected by search)
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                random_results_info = gr.Markdown("🎲 Discover Random Books", elem_classes="section-title")
                refresh_btn = gr.Button("🔄 Refresh Random", elem_classes="refresh-btn", size="sm")
            
            random_gallery = gr.Gallery(
                label="",
                show_label=False,
                elem_classes="scroll-horizontal",
                columns=100,  # Very large number to force horizontal scroll
                height=280,
                object_fit="cover"
            )
        
        # Popular Books Section (UNAFFECTED by search)
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_gallery = gr.Gallery(
                label="",
                show_label=False,
                elem_classes="scroll-horizontal",
                columns=100,
                height=280,
                object_fit="cover"
            )
            
            with gr.Row(elem_classes="load-more-container"):
                load_more_button = gr.Button("📚 Load More Popular Books", visible=False, variant="primary")
                page_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[random_gallery, popular_gallery, page_state, load_more_button, random_results_info]
    )
    
    load_more_button.click(
        load_more,
        inputs=[page_state, popular_gallery],
        outputs=[popular_gallery, page_state, load_more_button]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, random_gallery, popular_gallery, page_state, load_more_button, random_results_info]
    )
    
    refresh_btn.click(
        refresh_random,
        inputs=[search_box],
        outputs=[random_gallery, random_results_info]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[random_gallery, popular_gallery, page_state, load_more_button, random_results_info]
    )

if __name__ == "__main__":
    demo.launch()