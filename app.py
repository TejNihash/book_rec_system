import gradio as gr
import pandas as pd
import numpy as np
import ast
import random
import logging
import re

from sklearn.preprocessing import MultiLabelBinarizer, normalize
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics.pairwise import cosine_similarity

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
    for idx in indices or []:
        try:
            row = df.iloc[int(idx)]
        except Exception:
            continue
        caption = f"**{row['title']}**\nby {', '.join(row['authors'])}\n*{', '.join(row['genres'])}*"
        out.append((row.get("image_url", ""), caption))
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
        return [], []
    # defensive convert to ints & ensure valid
    liked_indices = [int(i) for i in liked_indices]
    valid = [i for i in liked_indices if 0 <= i < combined_matrix.shape[0]]
    if not valid:
        return [], []
    avg_embed = combined_matrix[valid].mean(axis=0)
    if hasattr(avg_embed, "A"):
        avg_vec = np.asarray(avg_embed.A1)
    else:
        avg_vec = np.asarray(avg_embed).ravel()
    sims = cosine_similarity(combined_matrix, avg_vec.reshape(1, -1)).ravel()
    ratings = df["average_rating"].fillna(0).values
    final_scores = ALPHA * ratings + (1 - ALPHA) * sims
    ranked_idx = np.argsort(final_scores)[::-1]
    recommended = [int(i) for i in ranked_idx if int(i) not in set(valid)][:top_n]
    gallery = make_gallery_data_from_indices(recommended)
    return gallery, recommended

# ---------------- SHELF FUNCTIONS ----------------
def random_gallery_init():
    indices = random.sample(list(df.index), min(PAGE_SIZE, len(df)))
    return make_gallery_data_from_indices(indices), indices, None

def search_random(query, genre_filter):
    filtered = filter_books(query, genre_filter)
    indices = list(filtered.index)
    if not indices:
        return [], [], None
    sampled = random.sample(indices, min(PAGE_SIZE, len(indices)))
    return make_gallery_data_from_indices(sampled), sampled, None

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

# ---------------- SELECTION (robust) ----------------
# --- selection handler (accepts value directly, not evt) ---
def set_selected(val):
    """
    val is the gallery item (tuple: (image_url, caption)) or just image_url.
    Returns the df index or None.
    """
    if val is None:
        logger.info("set_selected: val is None")
        return None

    logger.info(f"set_selected: got value={val}")

    img, caption = None, None
    if isinstance(val, (list, tuple)) and len(val) >= 1:
        img = val[0]
        caption = val[1] if len(val) > 1 else None
    elif isinstance(val, str):
        img = val
    elif isinstance(val, dict):
        img = val.get("image") or val.get("src") or val.get("image_url")
        caption = val.get("caption")

    # try to map by image_url
    if img:
        matches = df.index[df["image_url"] == img].tolist()
        if matches:
            df_idx = int(matches[0])
            logger.info(f"set_selected: matched image_url -> df_idx={df_idx}")
            return df_idx

    # fallback: try to parse title from caption
    if caption:
        import re
        m = re.search(r"\*\*(.*?)\*\*", caption)
        if m:
            title = m.group(1).strip()
            matches = df.index[df["title"] == title].tolist()
            if matches:
                df_idx = int(matches[0])
                logger.info(f"set_selected: matched caption title -> df_idx={df_idx}")
                return df_idx

    logger.warning("set_selected: could not map selection")
    return None


# ---------------- LIKE / RECOMMEND (robust) ----------------
def like_from_shelf(selected_idx, gallery_indices, liked_books, current_rec_indices):
    """
    Inputs:
      - selected_idx: value returned by set_selected (might be df-index OR gallery position OR None)
      - gallery_indices: the list of df indices currently shown in that gallery (best effort)
      - liked_books: current list of liked df-indices
      - current_rec_indices: current recommended indices list (so we can keep them if nothing changes)
    Returns:
      liked_books_state, liked_gallery (data for gallery), liked_indices_state,
      recommended_gallery (data), recommended_indices_state, reset_selected_state
    """
    liked_books = list(liked_books or [])
    gallery_indices = list(gallery_indices or [])
    current_rec_indices = list(current_rec_indices or [])

    logger.info(f"like_from_shelf called — selected_idx={selected_idx}, gallery_indices(len)={len(gallery_indices)}, liked_books={liked_books}")

    # No selection -> keep existing recs and liked gallery unchanged
    if selected_idx is None:
        logger.info("like_from_shelf: No selection -> keeping existing recs and liked gallery")
        liked_gallery = make_gallery_data_from_indices(liked_books)
        rec_gallery = make_gallery_data_from_indices(current_rec_indices)
        return liked_books, liked_gallery, liked_books, rec_gallery, current_rec_indices, None

    # Determine df_idx:
    df_idx = None
    try:
        # If selected_idx is already a df index present in df -> use it
        if int(selected_idx) in df.index:
            # but careful: selected_idx may be a gallery-position mapped to small integer that's also a valid df index.
            # Prefer mapping via gallery_indices when available:
            if selected_idx in gallery_indices:
                df_idx = int(selected_idx)
            else:
                # if gallery_indices provided and selected_idx is a position, map to corresponding df index
                if 0 <= int(selected_idx) < len(gallery_indices):
                    df_idx = int(gallery_indices[int(selected_idx)])
                else:
                    # as fallback, if selected_idx points to a valid df row (rare), accept it
                    if 0 <= int(selected_idx) < combined_matrix.shape[0]:
                        df_idx = int(selected_idx)
    except Exception:
        df_idx = None

    # Another attempt: if selected_idx not in df but gallery_indices available and selected_idx is a position
    if df_idx is None:
        try:
            pos = int(selected_idx)
            if 0 <= pos < len(gallery_indices):
                df_idx = int(gallery_indices[pos])
        except Exception:
            df_idx = None

    if df_idx is None:
        logger.warning("like_from_shelf: couldn't interpret selected index; keeping recs as-is")
        liked_gallery = make_gallery_data_from_indices(liked_books)
        rec_gallery = make_gallery_data_from_indices(current_rec_indices)
        return liked_books, liked_gallery, liked_books, rec_gallery, current_rec_indices, None

    # Add to liked list if new
    if df_idx not in liked_books:
        liked_books.append(df_idx)
        logger.info(f"like_from_shelf: added df_idx {df_idx} to liked_books -> {liked_books}")
    else:
        logger.info(f"like_from_shelf: df_idx {df_idx} already liked")

    liked_gallery = make_gallery_data_from_indices(liked_books)

    # compute recommendations using liked_books
    rec_gallery, rec_indices = get_recommendations_gallery(liked_books, top_n=20) if liked_books else (make_gallery_data_from_indices(current_rec_indices), current_rec_indices)

    # Reset selection for the gallery that triggered the like (return None for that selected_state)
    return liked_books, liked_gallery, liked_books, rec_gallery, rec_indices, None

# ---------------- INITIAL RECOMMENDATIONS ----------------
def init_recommendations():
    top_books = df.sort_values("average_rating", ascending=False).head(PAGE_SIZE)
    indices = list(top_books.index)
    gallery = make_gallery_data_from_indices(indices)
    return gallery, indices

# ---------------- UI ----------------
all_genres = sorted({g for sub in df["genres"] for g in sub})

with gr.Blocks() as demo:
    gr.HTML("""
    <style>
      .book-shelf {
          display: flex !important;
          overflow-x: auto !important;
          overflow-y: hidden !important;
          white-space: nowrap !important;
          height: 140px;
      }
      .book-shelf img {
          width: 80px;
          height: 120px;
          object-fit: cover;
          border-radius: 4px;
          margin: 4px;
          border: 2px solid transparent;
      }
      /* highlight selected */
      .book-shelf .gallery-selected img {
          border: 2px solid orange !important;
      }
      .section-title { margin-top: 12px; margin-bottom: 6px; }
    </style>
    """)

    # Search row
    with gr.Row():
        search_box = gr.Textbox(label="Search by title/author", placeholder="e.g. Dune, Aesop", value="")
        genre_dropdown = gr.Dropdown(label="Filter by genre", choices=all_genres, value=None, multiselect=False)

    # States
    random_indices_state = gr.State([])
    selected_random_state = gr.State(None)
    popular_indices_state = gr.State([])
    selected_popular_state = gr.State(None)
    popular_page_state = gr.State(0)
    recommended_indices_state = gr.State([])
    selected_recommended_state = gr.State(None)
    liked_books_state = gr.State([])
    liked_indices_state = gr.State([])

    # Random shelf
    gr.Markdown("<div class='section-title'>🎲 Random Books</div>")
    random_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    with gr.Row():
        random_like_btn = gr.Button("❤️ Like Selected (Random)")
        shuffle_random_btn = gr.Button("🔀 Shuffle Random")

    # Popular shelf
    gr.Markdown("<div class='section-title'>⭐ Popular Books</div>")
    popular_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    with gr.Row():
        load_more_popular_btn = gr.Button("Load More Popular")
        popular_like_btn = gr.Button("❤️ Like Selected (Popular)")

    # Recommended shelf
    gr.Markdown("<div class='section-title'>💡 Recommended Books</div>")
    recommended_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)
    recommended_like_btn = gr.Button("❤️ Like Selected (Recommended)")

    # Liked shelf
    gr.Markdown("<div class='section-title'>❤️ Liked Books</div>")
    liked_gallery = gr.Gallery(rows=1, columns=None, elem_classes="book-shelf", show_label=False, preview=True)

    # Initial loads
    demo.load(random_gallery_init, inputs=[], outputs=[random_gallery, random_indices_state, selected_random_state])
    demo.load(init_popular, inputs=[], outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])
    demo.load(init_recommendations, inputs=[], outputs=[recommended_gallery, recommended_indices_state])
    demo.load(lambda: ([], []), inputs=[], outputs=[liked_gallery, liked_indices_state])

    # Interactions
    search_box.submit(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state, selected_random_state])
    genre_dropdown.change(search_random, inputs=[search_box, genre_dropdown], outputs=[random_gallery, random_indices_state, selected_random_state])
    shuffle_random_btn.click(random_gallery_init, inputs=[], outputs=[random_gallery, random_indices_state, selected_random_state])

    load_more_popular_btn.click(load_more_popular, inputs=[popular_page_state, popular_indices_state],
                                outputs=[popular_gallery, popular_indices_state, popular_page_state, load_more_popular_btn])

    # IMPORTANT: set_selected expects only the event object. It will use evt.value (image+caption) to map to df index.
    random_gallery.select(set_selected, outputs=[selected_random_state])
    popular_gallery.select(set_selected, outputs=[selected_popular_state])
    recommended_gallery.select(set_selected, outputs=[selected_recommended_state])

    # Like buttons: pass gallery_indices and current_rec_indices so handler can map pos->df and preserve recs
    random_like_btn.click(
        like_from_shelf,
        inputs=[selected_random_state, random_indices_state, liked_books_state, recommended_indices_state],
        outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_random_state]
    )

    popular_like_btn.click(
        like_from_shelf,
        inputs=[selected_popular_state, popular_indices_state, liked_books_state, recommended_indices_state],
        outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_popular_state]
    )

    recommended_like_btn.click(
        like_from_shelf,
        inputs=[selected_recommended_state, recommended_indices_state, liked_books_state, recommended_indices_state],
        outputs=[liked_books_state, liked_gallery, liked_indices_state, recommended_gallery, recommended_indices_state, selected_recommended_state]
    )

# disable SSR to avoid inconsistent event signatures in some environments
demo.launch(ssr_mode=False)
