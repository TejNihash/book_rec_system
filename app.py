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
PAGE_SIZE = 20
MAX_BOOKS = 500

# Helper to filter dataset
def filter_books(query="", genre_filter=""):
    query = query.strip().lower()
    genre_filter = genre_filter.strip().lower()

    filtered = df.copy()

    if query:
        mask_title = filtered["title_lower"].str.contains(query)
        mask_authors = filtered["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = filtered["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = filtered[mask_title | mask_authors | mask_genres]

    if genre_filter:
        filtered = filtered[filtered["genres_lower"].apply(lambda lst: genre_filter in lst)]

    return filtered.head(MAX_BOOKS)

# Prepare gallery data
def make_gallery_data(filtered_df):
    return [
        (img, f"**{title}**\nby {', '.join(authors)}\n*{', '.join(genres)}*")
        for img, title, authors, genres in zip(
            filtered_df["image_url"], filtered_df["title"], filtered_df["authors"], filtered_df["genres"]
        )
    ]

# Initial load / search
def search_books(query, genre_filter):
    filtered = filter_books(query, genre_filter)
    page_data = filtered.iloc[:PAGE_SIZE]
    gallery_data = make_gallery_data(page_data)
    has_next = len(filtered) > PAGE_SIZE
    return gallery_data, 0, has_next

# Load next batch (infinite scroll)
def load_more_books(query, genre_filter, page, current_gallery):
    filtered = filter_books(query, genre_filter)
    start = (page + 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = filtered.iloc[start:end]
    new_gallery_data = make_gallery_data(page_data)
    gallery_data = current_gallery + new_gallery_data
    has_next = end < len(filtered)
    return gallery_data, page + 1, has_next

# Get all unique genres
all_genres = sorted({g for sublist in df["genres"] for g in sublist})

with gr.Blocks() as demo:
    # CSS to shrink gallery images
    gr.HTML("""
    <style>
        .small-gallery img {
            width: 120px;
            height: 180px;
            object-fit: cover;
        }
    </style>
    """)

    gr.Markdown("# 📚 My Book Showcase")

    with gr.Row():
        search_box = gr.Textbox(label="Search by title or author", placeholder="e.g. Asimov, Ender's game", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value="", multiselect=False)

    gallery = gr.Gallery(label="Books", show_label=False, columns=4, height="auto", elem_classes="small-gallery")

    load_more_button = gr.Button("Load More")

    # State for pagination
    page_state = gr.State(0)

    # Search triggers
    search_inputs = [search_box, genre_dropdown]
    search_outputs = [gallery, page_state, load_more_button]

    search_box.submit(search_books, inputs=search_inputs, outputs=search_outputs)
    genre_dropdown.change(search_books, inputs=search_inputs, outputs=search_outputs)

    # Load more button
    load_more_button.click(
        load_more_books,
        inputs=[search_box, genre_dropdown, page_state, gallery],
        outputs=[gallery, page_state, load_more_button]
    )

    # Hide button if no more books
    def toggle_button(has_next):
        return gr.update(visible=has_next)
    load_more_button.click(toggle_button, inputs=[load_more_button], outputs=[load_more_button])

demo.launch()
