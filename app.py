import gradio as gr
import pandas as pd
import numpy as np
import ast
import random

from sklearn.preprocessing import MultiLabelBinarizer, normalize
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics.pairwise import cosine_similarity

# -------------------- Configuration --------------------
DATA_CSV = "data_mini_books.csv"   # must match your repo file
DESC_EMB_PATH = "desc_embeds.npy"  # precomputed SBERT embeddings (same ordering as CSV)
PAGE_SIZE = 20
MAX_BOOKS = 500
ALPHA = 0.6   # weight on rating (0..1), 1->rating only, 0->similarity only

# -------------------- Load data --------------------
df = pd.read_csv(DATA_CSV)  # ensure this file exists in the repo

# expect authors/genres columns as Python lists (strings that eval to lists)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# lowercase helpers for search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# -------------------- Precomputed embeddings & MHE --------------------
desc_embeds = np.load(DESC_EMB_PATH)   # precomputed description embeddings

mlb_genres = MultiLabelBinarizer()
genre_matrix = mlb_genres.fit_transform(df["genres"])

mlb_authors = MultiLabelBinarizer()
author_matrix = mlb_authors.fit_transform(df["authors"])

# combine: desc (dense) as sparse + MHEs -> hstack -> normalize
desc_sparse = csr_matrix(desc_embeds)
combined_matrix = hstack([desc_sparse, csr_matrix(genre_matrix), csr_matrix(author_matrix)])
combined_matrix = normalize(combined_matrix)  # row-normalize for cosine similarity

# -------------------- Helper utilities --------------------
def make_gallery_data_from_indices(indices):
    """
    Return list of (image_url, caption) for the given dataframe indices.
    """
    out = []
    for idx in indices:
        row = df.iloc[idx]
        caption = f"**{row['title']}**\nby {', '.join(row['authors'])}\n*{', '.join(row['genres'])}*"
        out.append((row["image_url"], caption))
    return out

def filter_books(query="", genre_filter=""):
    """
    Returns a dataframe slice filtered by query (title/author) and genre. Capped at MAX_BOOKS.
    """
    q = (query or "").strip().lower()
    g = (genre_filter or "").strip().lower()
    filtered = df
    if q:
        mask_title = filtered["title_lower"].str.contains(q, na=False)
        mask_authors = filtered["authors_lower"].apply(lambda lst: any(q in a for a in lst))
        mask_genres = filtered["genres_lower"].apply(lambda lst: any(q in g for g in lst))
        filtered = filtered[mask_title | mask_authors | mask_genres]
    if g:
        filtered = filtered[filtered["genres_lower"].apply(lambda lst: g in lst)]
    return filtered.head(MAX_BOOKS)

# -------------------- Recommendation (hybrid) --------------------
def get_recommendations_gallery(liked_indices, top_n=20):
    """
    liked_indices: list of integer indices into df
    returns: (gallery_data_list, recommended_indices_list)
    """
    if not liked_indices:
        return [], []

    liked_indices = list(liked_indices)
    # average combined embedding of liked books
    avg_embed = combined_matrix[liked_indices].mean(axis=0)   # 1 x D (sparse or ndarray)
    # cosine similarity to all books
    sims = cosine_similarity(combined_matrix, avg_embed).ravel()  # shape (n_books,)

    # final score = ALPHA * rating + (1-ALPHA) * similarity
    ratings = df["average_rating"].fillna(0).values
    final_scores = ALPHA * ratings + (1 - ALPHA) * sims

    # sort books by final score, exclude liked ones
    ranked_idx = np.argsort(final_scores)[::-1]  # descending
    recommended = [i for i in ranked_idx if i not in liked_indices][:top_n]

    gallery_data = make_gallery_data_from_indices(recommended)
    return gallery_data, recommended

# -------------------- App functions (return gallery data + indices states) --------------------
def random_gallery_init(query="", genre_filter=""):
    """
    For random shelf: sample up to PAGE_SIZE items from filtered set.
    Returns (gallery_data, indices_list)
    """
    filtered = filter_books(query, genre_filter)
    indices = list(filtered.index)
    if len(indices) == 0:
        return [], []
    k = min(PAGE_SIZE, len(indices))
    sampled = random.sample(indices, k)
    return make_gallery_data_from_indices(sampled), sampled

def init_popular():
    """
    Initial popular page load (first PAGE_SIZE). Returns:
    (gallery_data, indices_list, next_page, gr.update(visible=has_next))
    """
    filtered = df.sort_values("average_rating", ascending=False).head(MAX_BOOKS)
    start = 0
    end = PAGE_SIZE
    indices = list(filtered.iloc[start:end].index)
    gallery = make_gallery_data_from_indices(indices)
    has_next = end < len(filtered)
    # next_page should be 1 because we consumed page 0
    return gallery, indices, 1, gr.update(visible=has_next)

def load_more_popular(page, current_indices):
    """
    page: current page number (1 means next chunk starts at PAGE_SIZE)
    current_indices: list of indices already displayed
    returns: (full_gallery_data_for_updated_indices, updated_indices, next_page, gr.update(visible=has_next))
    """
    filtered = df.sort_values("average_rating", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    new_indices = list(filtered.iloc[start:end].index)
    updated_indices = list(current_indices) + new_indices
    gallery = make_gallery_data_from_indices(updated_indices)
    has_next = end < len(filtered)
    return gallery, updated_indices, page + 1, gr.update(visible=has_next)

def search_random(query, genre_filter):
    """
    Called when user searches — update the random shelf with new random sample from filtered set.
    Returns (gallery_data, indices_list)
    """
    return random_gallery_init(query, genre_filter)

# -------------------- Like handler --------------------
def add_like(evt, gallery_indices, liked_books):
    """
    evt: SelectData event (automatically passed by .select)
    gallery_indices: list of dataset indices currently shown in that gallery
    liked_books: current liked_books state (list)
    Returns: updated liked_books state, recommended gallery data & indices, liked gallery data & indices
    """
    # if gallery_indices empty, nothing to do
    gallery_indices = list(gallery_indices or [])
    liked_books = list(liked_books or [])

    try:
        clicked_pos = evt.index  # index inside the currently shown gallery
    except Exception:
        # fallback: if evt has .value, try to map via image_url match
        val = evt.value if hasattr(evt, "value") else None
        if val:
            # val is usually image url or tuple (image, caption)
            image_url = val if isinstance(val, str) else (val[0] if isinstance(val, (list, tuple)) else None)
            if image_url:
                matches = [i for i in gallery_indices if df.iloc[i]["image_url"] == image_url]
                clicked_pos = 0
                if matches:
                    book_idx = matches[0]
                else:
                    return gr.update(), [], [], [], []  # no-op
            else:
                return gr.update(), [], [], [], []
        else:
            return gr.update(), [], [], [], []

    # convert to dataset index
    if clicked_pos is None or clicked_pos >= len(gallery_indices):
        return liked_books, [], [], [], []  # nothing changed

    book_idx = gallery_indices[clicked_pos]
    if book_idx not in liked_books:
        liked_books.append(int(book_idx))

    # update liked gallery
    liked_gallery_data = make_gallery_data_from_indices(liked_books)
    liked_gallery_indices = liked_books

    # recompute recommendations
    rec_data, rec_indices = get_recommendations_gallery(liked_books, top_n=20)

    # return updated liked_books state and galleries
    return liked_books, rec_data, rec_indices, liked_gallery_data, liked_gallery_indices

# -------------------- Build UI --------------------
all_genres = sorted({g for sublist in df["genres"] for g in sublist})

with gr.Blocks() as demo:
    # CSS for horizontal bookshelf
    gr.HTML("""
    <style>
        .book-shelf img {
            width: 120px;
            height: 180px;
            object-fit: cover;
            border-radius: 4px;
            margin: 6px;
        }
        /* ensure horizontal overflow behavior */
        .book-shelf .gallery-row {
            overflow-x: auto !important;
            overflow-y: hidden !important;
            white-space: nowrap;
        }
        /* small spacing below section titles */
        .section-title { margin-top: 18px; margin-bottom: 8px; }
    </style>
    """)

    # Top: search + genre
    with gr.Row():
        search_box = gr.Textbox(label="Search by title or author", placeholder="e.g. Aesop, Dune", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value=None, multiselect=False)

    # States
    random_indices_state = gr.State([])     # indices shown in random shelf
    popular_indices_state = gr.State([])    # indices shown in popular shelf
    recommended_indices_state = gr.State([]) # indices in recommended
    liked_indices_state = gr.State([])      # liked indices shown in liked gallery
    liked_books_state = gr.State([])        # liked book indices
    popular_page_state = gr.State(0)

    # Random shelf
    gr.Markdown("<div class='section-title'>### 🎲 Random Books</div>", elem_id="random_title")
    random_gallery = gr.Gallery(label="", rows=1, columns=None, elem_classes="book-shelf", show_label=False)

    # Popular shelf
    gr.Markdown("<div class='section-title'>### ⭐ Popular Books</div>", elem_id="popular_title")
    popular_gallery = gr.Gallery(label="", rows=1, columns=None, elem_classes="book-shelf", show_label=False)
    load_more_popular_btn = gr.Button("Load More Popular")

    # Recommended shelf
    gr.Markdown("<div class='section-title'>### 💡 Recommended Books</div>", elem_id="rec_title")
    recommended_gallery = gr.Gallery(label="", rows=1, columns=None, elem_classes="book-shelf", show_label=False)

    # Liked shelf (small)
    gr.Markdown("<div class='section-title'>### ❤️ Liked Books</div>", elem_id="liked_title")
    liked_gallery = gr.Gallery(label="", rows=1, columns=None, elem_classes="book-shelf", show_label=False)

    # -------------------- Initial loads --------------------
    # Random: initial random sample
    demo.load(random_gallery_init, inputs=[], outputs=[random_gallery, random_indices_state])

    # Popular: initial popular chunk, also set page state and Load More button visibility
    demo.load(init_popular, inputs=[], outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])

    # Recommended and Liked start empty
    demo.load(lambda: ([], []), inputs=[], outputs=[recommended_gallery, recommended_indices_state])
    demo.load(lambda: ([], []), inputs=[], outputs=[liked_gallery, liked_indices_state])

    # -------------------- Interactions --------------------
    # Search updates the Random shelf
    search_box.submit(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state])
    genre_dropdown.change(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state])

    # Popular Load More (appends)
    load_more_popular_btn.click(load_more_popular, inputs=[popular_page_state, popular_indices_state],
                                outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])

    # Clicking a cover in Random shelf -> like it
    random_gallery.select(add_like,
                          inputs=[random_indices_state, liked_books_state],
                          outputs=[liked_books_state, recommended_gallery, recommended_indices_state, liked_gallery, liked_indices_state])

    # Clicking a cover in Popular shelf -> like it
    popular_gallery.select(add_like,
                           inputs=[popular_indices_state, liked_books_state],
                           outputs=[liked_books_state, recommended_gallery, recommended_indices_state, liked_gallery, liked_indices_state])

demo.launch()
