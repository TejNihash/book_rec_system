import gradio as gr
import pandas as pd
import ast
import random

# ---------------- LOAD DATA ----------------
DATA_CSV = "data_mini_books.csv"
PAGE_SIZE = 20
MAX_BOOKS = 500

df = pd.read_csv(DATA_CSV)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# ---------------- HELPERS ----------------
def make_gallery_data_from_indices(indices):
    out = []
    for idx in indices:
        row = df.iloc[int(idx)]
        caption = f"**{row['title']}**\nby {', '.join(row['authors'])}\n*{', '.join(row['genres'])}*"
        out.append((row["image_url"], caption))
    if not out:
        out = [("https://via.placeholder.com/80x120?text=No+Books", "No books")]
    return out

def init_popular():
    """Return top popular books for the first page"""
    sorted_df = df.sort_values("ratings_count", ascending=False).head(MAX_BOOKS)
    indices = list(sorted_df.iloc[:PAGE_SIZE].index)
    return make_gallery_data_from_indices(indices), indices, 1

def load_more_popular(page, current_indices):
    """Load next PAGE_SIZE popular books"""
    sorted_df = df.sort_values("ratings_count", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    new_indices = list(sorted_df.iloc[start:end].index)
    updated_indices = list(current_indices or []) + new_indices
    return make_gallery_data_from_indices(updated_indices), updated_indices, page + 1

# ---------------- UI ----------------
with gr.Blocks() as demo:
    gr.Markdown("## 🔥 Popular Books Carousel")
    
    popular_gallery = gr.Gallery(
        label="Popular Books",
        rows=1,           # single row → horizontal scroll
        columns=None,
        show_label=False,
        elem_classes="book-shelf",
        preview=True
    )
    
    popular_indices_state = gr.State([])
    popular_page_state = gr.State(0)
    
    load_more_popular_btn = gr.Button("Load More Popular")
    
    # Load initial popular books
    demo.load(init_popular, inputs=[], outputs=[popular_gallery, popular_indices_state, popular_page_state])
    
    # Load next page on button click
    load_more_popular_btn.click(
        load_more_popular,
        inputs=[popular_page_state, popular_indices_state],
        outputs=[popular_gallery, popular_indices_state, popular_page_state]
    )

demo.launch()
