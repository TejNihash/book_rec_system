import gradio as gr
import pandas as pd
import numpy as np
import ast
from sklearn.preprocessing import MultiLabelBinarizer, normalize
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics.pairwise import cosine_similarity
import random

# ------------------- Load Dataset -------------------
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, image_url, average_rating

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# ------------------- Load Precomputed Embeddings -------------------
desc_embeds = np.load("desc_embeds.npy")  # precomputed BERT description embeddings

# Multi-hot encodings for genres & authors
mlb_genres = MultiLabelBinarizer()
genre_matrix = mlb_genres.fit_transform(df["genres"])

mlb_authors = MultiLabelBinarizer()
author_matrix = mlb_authors.fit_transform(df["authors"])

# Combine embeddings
desc_sparse = csr_matrix(desc_embeds)
combined_matrix = hstack([desc_sparse, genre_matrix, author_matrix])
combined_matrix = normalize(combined_matrix)

# ------------------- Constants -------------------
PAGE_SIZE = 20
MAX_BOOKS = 500
ALPHA = 0.6  # weight for average_rating in recommendation scoring

# ------------------- Helper Functions -------------------
def make_gallery_data(indices):
    data = []
    for idx in indices:
        row = df.iloc[idx]
        caption = f"**{row['title']}**\nby {', '.join(row['authors'])}\n*{', '.join(row['genres'])}*"
        data.append((row["image_url"], caption, idx))  # include idx for like button
    return data

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

# ------------------- Recommendation System -------------------
def get_recommendations(liked_books, top_n=15):
    if not liked_books:
        return []

    liked_indices = list(liked_books)
    avg_embed = combined_matrix[liked_indices].mean(axis=0)
    similarity = cosine_similarity(combined_matrix, avg_embed).flatten()

    # Exclude already liked books
    candidates = [i for i in range(len(df)) if i not in liked_indices]

    scores = []
    for i in candidates:
        score = ALPHA * df.iloc[i]["average_rating"] + (1 - ALPHA) * similarity[i]
        scores.append((i, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [i for i, _ in scores[:top_n]]
    return make_gallery_data(top_indices)

# ------------------- Gradio Functions -------------------
def get_random_books(query="", genre_filter=""):
    filtered = filter_books(query, genre_filter)
    indices = random.sample(list(filtered.index), min(PAGE_SIZE, len(filtered)))
    return make_gallery_data(indices)

def get_popular_books(page=0):
    filtered = df.sort_values("average_rating", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    indices = list(filtered.iloc[start:end].index)
    has_next = end < len(filtered)
    return make_gallery_data(indices), page + 1, has_next

def load_more_popular(page, current_gallery):
    new_data, next_page, has_next = get_popular_books(page)
    return current_gallery + new_data, next_page, has_next

def search_random_books(query, genre_filter):
    return get_random_books(query, genre_filter)

def add_like(book_idx, liked_books):
    liked_books = list(liked_books)
    if book_idx not in liked_books:
        liked_books.append(book_idx)
    return liked_books, get_recommendations(liked_books)

# ------------------- Build Gradio App -------------------
all_genres = sorted({g for sublist in df["genres"] for g in sublist})

with gr.Blocks() as demo:
    gr.HTML("""
    <style>
        .small-gallery img { width:120px; height:180px; object-fit:cover; }
    </style>
    """)

    # ---------------- Top Search ----------------
    with gr.Row():
        search_box = gr.Textbox(label="Search by title or author", placeholder="e.g. Aesop, Dune", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value=None, multiselect=False)

    liked_books_state = gr.State([])  # store indices of liked books
    popular_page_state = gr.State(0)

    # ---------------- Random Books ----------------
    gr.Markdown("### 🎲 Random Books")
    random_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")

    # ---------------- Popular Books ----------------
    gr.Markdown("### ⭐ Popular Books")
    popular_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")
    load_more_popular_btn = gr.Button("Load More Popular")

    # ---------------- Recommended Books ----------------
    gr.Markdown("### 💡 Recommended Books")
    recommended_gallery = gr.Gallery(label="", columns=3, elem_classes="small-gallery")

    # ---------------- Callbacks ----------------
    # Initial load
    demo.load(lambda: get_random_books(), outputs=random_gallery)
    demo.load(lambda: get_popular_books(), outputs=[popular_gallery, popular_page_state, load_more_popular_btn])

    # Search updates random section
    search_box.submit(search_random_books, inputs=[search_box, genre_dropdown], outputs=random_gallery)
    genre_dropdown.change(search_random_books, inputs=[search_box, genre_dropdown], outputs=random_gallery)

    # Load more popular
    load_more_popular_btn.click(load_more_popular, inputs=[popular_page_state, popular_gallery],
                                outputs=[popular_gallery, popular_page_state, load_more_popular_btn])

    # Like buttons for all galleries
    # Gradio doesn't allow embedding button per gallery item, so we simulate by returning index on click
    # We'll use `select` event: when a gallery item is clicked, treat it as "like"
    random_gallery.select(add_like, inputs=[gr.State(lambda x: x), liked_books_state],
                          outputs=[liked_books_state, recommended_gallery])
    popular_gallery.select(add_like, inputs=[gr.State(lambda x: x), liked_books_state],
                           outputs=[liked_books_state, recommended_gallery])

demo.launch()
