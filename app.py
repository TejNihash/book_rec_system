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

def get_random_books(n=RANDOM_SAMPLE_SIZE):
    """Get random sample of books"""
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=42)  # Fixed seed for consistency during session

def search_books(query="", page=0):
    """Filter + paginate dataset for popular books section"""
    query = query.strip().lower()
    
    # Filter dataset
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        # Show popular books by default (first N books)
        filtered = df
    
    # Optional: show only top 500 results for performance
    filtered = filtered.head(500)
    
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
    # Random books (always show random, unaffected by search)
    random_books = get_random_books()
    random_gallery = prepare_gallery_data(random_books)
    
    # Popular books (affected by search)
    popular_gallery, has_next, total_results = search_books(query, page=0)
    
    if query:
        results_text = f"🔍 Found {total_results} books for '{query}'"
    else:
        results_text = "📚 Popular Books"
    
    return random_gallery, popular_gallery, 0, gr.update(visible=has_next), results_text

# Load more functionality for popular books
def load_more(query, page, current_popular_gallery):
    page += 1
    gallery_data, has_next, total_results = search_books(query, page)
    # Append new results to existing gallery
    new_gallery = current_popular_gallery + gallery_data
    return new_gallery, page, gr.update(visible=has_next)

# Refresh random books
def refresh_random():
    random_books = get_random_books()
    random_gallery = prepare_gallery_data(random_books)
    return random_gallery

# Clear search - resets to default view
def clear_search():
    return "", *initial_load("")

# Build UI with two sections
with gr.Blocks(css="""
    .scroll-gallery {
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 15px;
        min-height: 280px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
    }
    .scroll-gallery .thumbnail {
        flex: 0 0 auto;
        width: 160px;
        height: 240px;
        object-fit: cover;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .scroll-gallery .thumbnail:hover {
        transform: scale(1.05);
    }
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .section-title {
        font-size: 1.4em;
        font-weight: bold;
        color: #333;
    }
    .results-info {
        font-size: 14px;
        color: #666;
        margin: 10px 0;
        font-weight: bold;
    }
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .refresh-btn {
        background: #4CAF50;
        color: white;
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
                placeholder="🔍 Search by title, author, or genre...",
                value="",
                scale=4
            )
            clear_btn = gr.Button("Clear Search", scale=1, variant="secondary")
        
        # Random Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("### 🎲 Discover Random Books", elem_classes="section-title")
                refresh_btn = gr.Button("🔄 Refresh Random", elem_classes="refresh-btn", size="sm")
            
            random_gallery = gr.Gallery(
                label="",
                show_label=False,
                elem_classes="scroll-gallery",
                columns=20,  # Large number for horizontal scroll
                height=260
            )
        
        # Popular Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                results_info = gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_gallery = gr.Gallery(
                label="",
                show_label=False,
                elem_classes="scroll-gallery",
                columns=20,
                height=260
            )
            
            with gr.Row():
                load_more_button = gr.Button("📚 Load More Books", visible=False, variant="primary")
                page_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[random_gallery, popular_gallery, page_state, load_more_button, results_info]
    )
    
    load_more_button.click(
        load_more,
        inputs=[search_box, page_state, popular_gallery],
        outputs=[popular_gallery, page_state, load_more_button]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, random_gallery, popular_gallery, page_state, load_more_button, results_info]
    )
    
    refresh_btn.click(
        refresh_random,
        outputs=[random_gallery]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[random_gallery, popular_gallery, page_state, load_more_button, results_info]
    )

if __name__ == "__main__":
    demo.launch()