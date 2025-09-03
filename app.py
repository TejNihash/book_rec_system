import gradio as gr
import pandas as pd
import numpy as np
import ast
import random
import logging

from sklearn.preprocessing import MultiLabelBinarizer, normalize
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
DATA_CSV = "data_mini_books.csv"
DESC_EMB_PATH = "desc_embeds.npy"
PAGE_SIZE = 20
MAX_BOOKS = 500
ALPHA = 0.6  # weight for rating in hybrid score

# ---------------- LOAD DATA ----------------
df = pd.read_csv(DATA_CSV)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# ---------------- EMBEDDINGS & MHE ----------------
desc_embeds = np.load(DESC_EMB_PATH)
mlb_genres = MultiLabelBinarizer()
genre_matrix = mlb_genres.fit_transform(df["genres"])
mlb_authors = MultiLabelBinarizer()
author_matrix = mlb_authors.fit_transform(df["authors"])

desc_sparse = csr_matrix(desc_embeds)
combined_matrix = hstack([desc_sparse, csr_matrix(genre_matrix), csr_matrix(author_matrix)])
combined_matrix = normalize(combined_matrix)

# ---------------- HELPERS ----------------
def make_gallery_data_from_indices(indices):
    out = []
    for idx in indices:
        row = df.iloc[int(idx)]
        caption = f"**{row['title']}**\nby {', '.join(row['authors'])}\n*{', '.join(row['genres'])}*"
        out.append((row["image_url"], caption))
    return out

def filter_books(query="", genre_filter=""):
    q = (query or "").strip().lower()
    g = (genre_filter or "").strip().lower()
    filtered = df
    if q:
        mask_title = filtered["title_lower"].str.contains(q, na=False)
        mask_authors = filtered["authors_lower"].apply(lambda lst: any(q in a for a in lst))
        mask_genres = filtered["genres_lower"].apply(lambda lst: any(q in item for item in lst))
        filtered = filtered[mask_title | mask_authors | mask_genres]
    if g:
        filtered = filtered[filtered["genres_lower"].apply(lambda lst: g in lst)]
    return filtered.head(MAX_BOOKS)

# ---------------- RECOMMENDER ----------------
def get_recommendations_gallery(liked_indices, top_n=20):
    if not liked_indices:
        # fallback: top rated books
        top_df = df.sort_values("average_rating", ascending=False).head(top_n)
        indices = list(top_df.index)
        return make_gallery_data_from_indices(indices), indices

    avg_embed = combined_matrix[liked_indices].mean(axis=0)
    if hasattr(avg_embed, "A"):
        avg_vec = np.asarray(avg_embed.A1)
    else:
        avg_vec = np.asarray(avg_embed).ravel()
    sims = cosine_similarity(combined_matrix, avg_vec.reshape(1, -1)).ravel()
    ratings = df["average_rating"].fillna(0).values
    final_scores = ALPHA * ratings + (1 - ALPHA) * sims
    ranked_idx = np.argsort(final_scores)[::-1]
    recommended = [int(i) for i in ranked_idx if i not in liked_indices][:top_n]
    gallery = make_gallery_data_from_indices(recommended)
    return gallery, recommended

# ---------------- SHELF FUNCTIONS ----------------
def random_gallery_init():
    indices = random.sample(list(df.index), min(PAGE_SIZE, len(df)))
    return make_gallery_data_from_indices(indices), indices

def search_random(query, genre_filter):
    filtered = filter_books(query, genre_filter)
    indices = list(filtered.index)
    if not indices:
        return [], []
    sampled = random.sample(indices, min(PAGE_SIZE, len(indices)))
    return make_gallery_data_from_indices(sampled), sampled

def init_popular():
    sorted_df = df.sort_values("ratings_count", ascending=False).head(MAX_BOOKS)
    indices = list(sorted_df.iloc[:PAGE_SIZE].index)
    gallery = make_gallery_data_from_indices(indices)
    has_next = PAGE_SIZE < len(sorted_df)
    return gallery, indices, 1, gr.update(visible=has_next)

def load_more_popular(page, current_indices):
    sorted_df = df.sort_values("ratings_count", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    new_indices = list(sorted_df.iloc[start:end].index)
    updated_indices = list(current_indices or []) + new_indices
    gallery = make_gallery_data_from_indices(updated_indices)
    has_next = end < len(sorted_df)
    return gallery, updated_indices, page + 1, gr.update(visible=has_next)

# ---------------- SELECTION HANDLER ----------------
def set_selected(gallery_item):
    """
    Receives a selected gallery item (image_url, caption tuple) and maps to df index.
    """
    if gallery_item is None:
        logger.info("set_selected: no item selected")
        return None
    img_url = gallery_item[0]
    match = df.index[df["image_url"] == img_url]
    if not match.empty:
        idx = int(match[0])
        logger.info(f"set_selected: mapped image_url to df index {idx}")
        return idx
    logger.warning("set_selected: could not map image_url")
    return None


# ---------------- LIKE HANDLER ----------------
def like_from_shelf(selected_idx, gallery_indices, liked_books):
    if selected_idx is None:
        return liked_books, make_gallery_data_from_indices(liked_books), liked_books, *get_recommendations_gallery(liked_books), None

    df_idx = selected_idx
    liked_books = list(liked_books or [])
    if df_idx not in liked_books:
        liked_books.append(df_idx)

    liked_gallery = make_gallery_data_from_indices(liked_books)
    rec_gallery, rec_indices = get_recommendations_gallery(liked_books)
    return liked_books, liked_gallery, liked_books, rec_gallery, rec_indices, None

# ---------------- UI ----------------
all_genres = sorted({g for sub in df["genres"] for g in sub})

with gr.Blocks() as demo:
    gr.HTML("""
    <style>
      .book-shelf { display: flex !important; overflow-x: auto !important; overflow-y: hidden !important; white-space: nowrap !important; height: 140px; }
      .book-shelf img { width: 80px; height: 120px; object-fit: cover; border-radius: 4px; margin: 4px; }
      .book-shelf .gallery-selected img { border: 3px solid orange; }
    </style>
    """)

    with gr.Row():
        search_box = gr.Textbox(label="Search by title/author", placeholder="e.g. Dune, Aesop", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value=None, multiselect=False)

    # States
    random_indices_state = gr.State([])
    popular_indices_state = gr.State([])
    popular_page_state = gr.State(0)
    recommended_indices_state = gr.State([])
    liked_books_state = gr.State([])
    liked_indices_state = gr.State([])

    selected_random_state = gr.State(None)
    selected_popular_state = gr.State(None)
    selected_recommended_state = gr.State(None)

    # ---------------- Random ----------------
    gr.Markdown("🎲 Random Books")
    random_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    with gr.Row():
        random_like_btn = gr.Button("❤️ Like Selected (Random)")
        shuffle_random_btn = gr.Button("🔀 Shuffle Random")

    # ---------------- Popular ----------------
    gr.Markdown("⭐ Popular Books")
    popular_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    with gr.Row():
        load_more_popular_btn = gr.Button("Load More Popular")
        popular_like_btn = gr.Button("❤️ Like Selected (Popular)")

    # ---------------- Recommended ----------------
    gr.Markdown("💡 Recommended Books")
    recommended_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    recommended_like_btn = gr.Button("❤️ Like Selected (Recommended)")

    # ---------------- Liked ----------------
    gr.Markdown("❤️ Liked Books")
    liked_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)

    # ---------------- INITIAL LOADS ----------------
    demo.load(random_gallery_init, inputs=[], outputs=[random_gallery, random_indices_state])
    demo.load(init_popular, inputs=[], outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])
    demo.load(lambda: get_recommendations_gallery([]), inputs=[], outputs=[recommended_gallery, recommended_indices_state])
    demo.load(lambda: ([], []), inputs=[], outputs=[liked_gallery, liked_indices_state])

    # ---------------- INTERACTIONS ----------------
    search_box.submit(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state])
    genre_dropdown.change(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state])
    shuffle_random_btn.click(random_gallery_init, inputs=[], outputs=[random_gallery, random_indices_state])

    load_more_popular_btn.click(load_more_popular, inputs=[popular_page_state, popular_indices_state],
                                outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])

    # gallery selection handlers
    random_gallery.select(set_selected, inputs=[random_gallery], outputs=[selected_random_state])
    popular_gallery.select(set_selected, inputs=[popular_gallery], outputs=[selected_popular_state])
    recommended_gallery.select(set_selected, inputs=[recommended_gallery], outputs=[selected_recommended_state])

    # like buttons
    random_like_btn.click(like_from_shelf,
                          inputs=[selected_random_state, random_indices_state, liked_books_state],
                          outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_random_state])

    popular_like_btn.click(like_from_shelf,
                           inputs=[selected_popular_state, popular_indices_state, liked_books_state],
                           outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_popular_state])

    recommended_like_btn.click(like_from_shelf,
                               inputs=[selected_recommended_state, recommended_indices_state, liked_books_state],
                               outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_recommended_state])

demo.launch(ssr_mode=False)
