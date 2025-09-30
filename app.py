import gradio as gr
import pandas as pd
import ast

# ---------------- LOAD DATA ----------------
DATA_CSV = "data_mini_books.csv"
PAGE_SIZE = 4  # show 4 books per page
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

def get_popular_page(page):
    """Return PAGE_SIZE popular books for the given page"""
    sorted_df = df.sort_values("ratings_count", ascending=False).head(MAX_BOOKS)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    indices = list(sorted_df.iloc[start:end].index)
    return make_gallery_data_from_indices(indices), indices, page

# ---------------- UI ----------------
with gr.Blocks() as demo:
    gr.Markdown("## 🔥 Popular Books Shelf (4 per row)")

    popular_gallery = gr.Gallery(
        label="Popular Books",
        rows=1,        # single row
        columns=4,     # show exactly 4 books
        show_label=False,
        elem_classes="book-shelf",
        preview=True
    )

    popular_indices_state = gr.State([])
    popular_page_state = gr.State(0)

    next_btn = gr.Button("➡️ Next")

    # Initial load
    demo.load(get_popular_page, inputs=[gr.State(0)], outputs=[popular_gallery, popular_indices_state, popular_page_state])

    # Click Next to load the next 4 books
    next_btn.click(get_popular_page,
                   inputs=[gr.State(lambda: popular_page_state.value + 1)],
                   outputs=[popular_gallery, popular_indices_state, popular_page_state])

demo.launch()
