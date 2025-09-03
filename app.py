import gradio as gr
import pandas as pd
import ast

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, image_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Precompute lowercase for faster search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Pagination settings
PAGE_SIZE = 20  # number of books per page

def search_books(query, page=0):
    query = query.strip().lower()
    
    # Filter dataset
    if query:
        mask_title = df["title_lower"].str.contains(query)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df

    # Optional: show only top 500 results for performance
    filtered = filtered.head(500)
    
    # Pagination
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = filtered.iloc[start:end]

    # Prepare gallery data
    gallery_data = [
        (img, f"**{title}**\nby {', '.join(authors)}\n*{', '.join(genres)}*")
        for img, title, authors, genres in zip(
            page_data["image_url"], page_data["title"], page_data["authors"], page_data["genres"]
        )
    ]
    
    # Return gallery + next page availability
    has_next = end < len(filtered)
    return gallery_data, has_next

# For handling "Load More" button
def load_more(query, page):
    page += 1
    gallery_data, has_next = search_books(query, page)
    return gallery_data, page, has_next

with gr.Blocks() as demo:
    gr.Markdown("# 📚 My Book Showcase")
    
    search_box = gr.Textbox(
        label="Search by title, author, or genre",
        placeholder="e.g. Aesop, fantasy, Dune...",
        value=""
    )
    
    gallery = gr.Gallery(
        label="Books", show_label=False, columns=3, height="auto", scroll=True
    )
    
    load_more_button = gr.Button("Load More")
    
    # Hidden state to track current page
    page_state = gr.State(0)
    
    # Initial search/load
    def initial_load(query):
        gallery_data, has_next = search_books(query, page=0)
        return gallery_data, 0, has_next
    
    search_box.submit(initial_load, inputs=search_box, outputs=[gallery, page_state, load_more_button])
    
    # Load more functionality
    load_more_button.click(load_more, inputs=[search_box, page_state], outputs=[gallery, page_state, load_more_button])
    
    # Hide "Load More" button if no next page
    def toggle_load_more(has_next):
        return gr.update(visible=has_next)
    
    load_more_button.click(toggle_load_more, inputs=[load_more_button], outputs=[load_more_button])

demo.launch()
