import gradio as gr
import pandas as pd
import ast
import random

# ------------------- Load Dataset -------------------
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, image_url, average_rating

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

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

def get_random_books():
    sample_df = df.sample(min(PAGE_SIZE, len(df)))
    return make_gallery_data(sample_df)

def get_popular_books(page=0, current_gallery=[]):
    filtered = df.sort_values("average_rating", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = filtered.iloc[start:end]
    new_gallery_data = make_gallery_data(page_data)
    gallery_data = current_gallery + new_gallery_data
    has_next = end < len(filtered)
    return gallery_data, page + 1, has_next

def search_books(query, genre_filter):
    filtered = filter_books(query, genre_filter)
    page_data = filtered.iloc[:PAGE_SIZE]
    gallery_data = make_gallery_data(page_data)
    has_next = len(filtered) > PAGE_SIZE
    return gallery_data, 0, has_next

def load_more_popular(page, current_gallery):
    return get_popular_books(page, current_gallery)

def load_more_search(query, genre_filter, page, current_gallery):
    filtered = filter_books(query, genre_filter)
    start = (page + 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = filtered.iloc[start:end]
    new_gallery_data = make_gallery_data(page_data)
    gallery_data = current_gallery + new_gallery_data
    has_next = end < len(filtered)
    return gallery_data, page + 1, has_next

# ------------------- Gradio App -------------------
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

    # ---------- Random Books Section ----------
    gr.Markdown("### 🎲 Random Books")
    random_gallery = gr.Gallery(get_random_books(), label="", columns=3, elem_classes="small-gallery")

    # ---------- Popular Books Section ----------
    gr.Markdown("### ⭐ Popular Books")
    popular_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")
    popular_page_state = gr.State(0)
    load_more_popular_button = gr.Button("Load More Popular")

    # Initialize popular gallery on load
    def init_popular():
        data, page, has_next = get_popular_books()
        return data, page, gr.update(visible=has_next)
    demo.load(init_popular, inputs=[], outputs=[popular_gallery, popular_page_state, load_more_popular_button])

    load_more_popular_button.click(
        load_more_popular,
        inputs=[popular_page_state, popular_gallery],
        outputs=[popular_gallery, popular_page_state, load_more_popular_button]
    )

    # ---------- Search Section ----------
    gr.Markdown("### 🔍 Search Books")
    with gr.Row():
        search_box = gr.Textbox(label="Search by title or author", placeholder="e.g. Aesop, Dune", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value=None, multiselect=False)
    search_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")
    search_page_state = gr.State(0)
    load_more_search_button = gr.Button("Load More Search Results")

    search_inputs = [search_box, genre_dropdown]
    search_outputs = [search_gallery, search_page_state, load_more_search_button]
    search_box.submit(search_books, inputs=search_inputs, outputs=search_outputs)
    genre_dropdown.change(search_books, inputs=search_inputs, outputs=search_outputs)

    load_more_search_button.click(
        load_more_search,
        inputs=[search_box, genre_dropdown, search_page_state, search_gallery],
        outputs=[search_gallery, search_page_state, load_more_search_button]
    )

demo.launch()
