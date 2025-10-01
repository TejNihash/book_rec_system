import ast
import pandas as pd
import gradio as gr

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
PAGE_SIZE = 20  # number of books per page

def search_books(query="", page=0):
    """Filter + paginate dataset"""
    query = query.strip().lower()
    
    # Filter dataset
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        # Show popular books by default (first N books, or you could sort by rating if available)
        filtered = df
    
    # Optional: show only top 500 results for performance
    filtered = filtered.head(500)
    
    # Pagination
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
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

# Initial load - show default books
def initial_load(query=""):
    gallery_data, has_next, total_results = search_books(query, page=0)
    results_text = f"Found {total_results} books" if query else "Popular Books"
    return gallery_data, 0, gr.update(visible=has_next), results_text

# Load more functionality
def load_more(query, page, current_gallery):
    page += 1
    gallery_data, has_next, total_results = search_books(query, page)
    # Append new results to existing gallery
    new_gallery = current_gallery + gallery_data
    return new_gallery, page, gr.update(visible=has_next)

# Clear search and show default books
def clear_search():
    return "", initial_load("")

# Build UI with improved styling
with gr.Blocks(css="""
    .scroll-gallery {
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 15px;
        min-height: 300px;
    }
    .scroll-gallery .thumbnail {
        flex: 0 0 auto;
        width: 180px;
        height: 280px;
        object-fit: cover;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 10px;
        margin: 10px 0;
    }
    .results-info {
        font-size: 14px;
        color: #666;
        margin: 10px 0;
        font-weight: bold;
    }
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
""") as demo:
    
    with gr.Column():
        with gr.Row():
            with gr.Column():
                gr.Markdown("""
                # 📚 Book Explorer
                *Discover your next favorite read*
                """, elem_classes="search-header")
        
        with gr.Row():
            search_box = gr.Textbox(
                label="",
                placeholder="🔍 Search by title, author, or genre...",
                value="",
                scale=4
            )
            clear_btn = gr.Button("Clear", scale=1)
        
        results_info = gr.Markdown("Popular Books", elem_classes="results-info")
        
        with gr.Column(elem_classes="gallery-container"):
            gallery = gr.Gallery(
                label="",
                show_label=False,
                elem_classes="scroll-gallery",
                columns=10,  # This helps with horizontal layout
                height=320
            )
        
        with gr.Row():
            load_more_button = gr.Button("📚 Load More Books", visible=False, variant="secondary")
            page_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[gallery, page_state, load_more_button, results_info]
    )
    
    load_more_button.click(
        load_more,
        inputs=[search_box, page_state, gallery],
        outputs=[gallery, page_state, load_more_button]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, gallery, page_state, load_more_button, results_info]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[gallery, page_state, load_more_button, results_info]
    )

if __name__ == "__main__":
    demo.launch()