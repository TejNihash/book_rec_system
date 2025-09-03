import gradio as gr
import pandas as pd
import ast
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, image_url, average_rating

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Precompute lowercase for faster search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

PAGE_SIZE = 20
MAX_BOOKS = 500

# ------------------- Helpers -------------------
def make_gallery_data(filtered_df):
    return [
        (img, f"**{title}**\nby {', '.join(authors)}\n*{', '.join(genres)}*")
        for img, title, authors, genres in zip(
            filtered_df["image_url"], filtered_df["title"], filtered_df["authors"], filtered_df["genres"]
        )
    ]

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

# Random books for initial section
def get_random_books():
    sample_df = df.sample(min(PAGE_SIZE, len(df)))
    return make_gallery_data(sample_df)

# Popular books based on average_rating
def get_popular_books(page=0, current_gallery=[]):
    filtered = df.sort_values("average_rating", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = filtered.iloc[start:end]
    new_gallery_data = make_gallery_data(page_data)
    gallery_data = current_gallery + new_gallery_data
    has_next = end < len(filtered)
    return gallery_data, page + 1, has_next

# Search + genre filtering
def search_books(query, genre_filter):
    filtered = filter_books(query, genre_filter)
    page_data = filtered.iloc[:PAGE_SIZE]
    gallery_data = make_gallery_data(page_data)
    has_next = len(filtered) > PAGE_SIZE
    return gallery_data, 0, has_next

# Load more popular books
def load_more_popular(page, current_gallery):
    return get_popular_books(page, current_gallery)

# ------------------- Gradio App -------------------
all_genres = sorted({g for sublist in df["genres"] for g in sublist})

with gr.Blocks() as demo:
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

    # Random section
    gr.Markdown("### 🎲 Random Books")
    random_gallery = gr.Gallery(make_gallery_data(df.sample(PAGE_SIZE)), label="", columns=3, elem_classes="small-gallery")

    # Popular section
    gr.Markdown("### ⭐ Popular Books")
    popular_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")
    popular_page_state = gr.State(0)
    load_more_button = gr.Button("Load More Popular")

    # Search section
    gr.Markdown("### 🔍 Search Books")
    with gr.Row():
        search_box = gr.Textbox(label="Search by title or author", placeholder="e.g. Aesop, Dune", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value="", multiselect=False)
    search_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")
    search_page_state = gr.State(0)
    search_load_more_button = gr.Button("Load More Search Results")

    # ------------------- Callbacks -------------------
    # Initial popular load
    def init_popular():
        data, page, has_next = get_popular_books()
        return data, page, gr.update(visible=has_next)
    init_popular_gallery = init_popular()
    popular_gallery.update(init_popular_gallery[0])
    popular_page_state.set(init_popular_gallery[1])
    load_more_button.update(init_popular_gallery[2])

    # Load more popular
    load_more_button.click(load_more_popular, inputs=[popular_page_state, popular_gallery],
                           outputs=[popular_gallery, popular_page_state, load_more_button])

    # Search triggers
    search_inputs = [search_box, genre_dropdown]
    search_outputs = [search_gallery, search_page_state, search_load_more_button]
    search_box.submit(search_books, inputs=search_inputs, outputs=search_outputs)
    genre_dropdown.change(search_books, inputs=search_inputs, outputs=search_outputs)

    # Load more search results
    search_load_more_button.click(load_more_popular, inputs=[search_page_state, search_gallery],
                                  outputs=[search_gallery, search_page_state, search_load_more_button])

demo.launch()
