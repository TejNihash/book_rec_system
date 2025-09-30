import gradio as gr
import pandas as pd
import ast
import random

# ---------------- LOAD DATA ----------------
DATA_CSV = "data_mini_books.csv"

df = pd.read_csv(DATA_CSV)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# ---------------- HELPERS ----------------
def make_gallery_data_from_indices(indices):
    out = []
    for idx in indices:
        row = df.iloc[int(idx)]
        caption = f"{row['title']}\nby {', '.join(row['authors'])}\n{', '.join(row['genres'])}"
        out.append((row["image_url"], caption))
    if not out:
        out = [("https://via.placeholder.com/80x120?text=No+Books", "No books")]
    return out

def get_popular_books():
    sorted_df = df.sort_values("ratings_count", ascending=False)
    top_indices = list(sorted_df.head(20).index)  # show top 20
    return make_gallery_data_from_indices(top_indices), top_indices

# ---------------- UI ----------------
with gr.Blocks() as demo:
    gr.Markdown("## 🔥 Popular Books Carousel")

    popular_gallery = gr.Gallery(
        label="Popular Books",
        rows=1,        # single horizontal row
        columns=None,  # auto-fit
        show_label=False,
        elem_classes="book-shelf",
        preview=True
    )

    popular_indices_state = gr.State([])

    # Load popular books at startup
    demo.load(get_popular_books, inputs=[], outputs=[popular_gallery, popular_indices_state])

demo.launch()
