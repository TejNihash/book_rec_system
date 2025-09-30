import gradio as gr
import pandas as pd
import ast

# ---------------- LOAD DATA ----------------
DATA_CSV = "data_mini_books.csv"

df = pd.read_csv(DATA_CSV)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# ---------------- HELPERS ----------------
def make_gallery_data(indices):
    out = []
    for idx in indices:
        row = df.iloc[int(idx)]
        caption = f"{row['title']}\nby {', '.join(row['authors'])}"
        out.append((row["image_url"], caption))
    return out

def get_popular_books():
    sorted_df = df.sort_values("ratings_count", ascending=False)
    top_indices = list(sorted_df.head(20).index)
    return make_gallery_data(top_indices), top_indices

# ---------------- UI ----------------
with gr.Blocks(css="""
.book-shelf .gr-gallery-item {
    border: 2px solid #ddd;
    border-radius: 8px;
    padding: 5px;
    margin: 5px;
    text-align: center;
    box-shadow: 2px 2px 6px #ccc;
}
.book-shelf .gr-gallery-item img {
    width: 120px;
    height: 180px;
    object-fit: cover;
}
""") as demo:
    gr.Markdown("## 🔥 Popular Books Carousel")

    popular_gallery = gr.Gallery(
        label="Popular Books",
        rows=1,
        columns=None,   # auto-fit multiple books
        show_label=False,
        elem_classes="book-shelf",
        preview=True
    )

    popular_indices_state = gr.State([])

    demo.load(get_popular_books, inputs=[], outputs=[popular_gallery, popular_indices_state])

demo.launch()
