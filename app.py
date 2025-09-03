import gradio as gr
import pandas as pd
import ast

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, img_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

def search_books(query):
    query = query.strip().lower()
    if query:
        filtered = df[
            df.apply(
                lambda row: (
                    query in row["title"].lower()
                    or any(query in a.lower() for a in row["authors"])
                    or any(query in g.lower() for g in row["genres"])
                ),
                axis=1,
            )
        ]
    else:
        filtered = df
    
    # Build gallery items
    gallery_data = []
    for _, row in filtered.iterrows():
        authors_str = ", ".join(row["authors"])
        genres_str = ", ".join(row["genres"])
        caption = f"**{row['title']}**\nby {authors_str}\n*{genres_str}*"
        gallery_data.append([row["image_url"], caption])
    
    return gallery_data

with gr.Blocks() as demo:
    gr.Markdown("# 📚 My Book Showcase")
    
    with gr.Row():
        search_box = gr.Textbox(
            label="Search by title, author, or genre",
            placeholder="e.g. Aesop, fantasy, Dune..."
        )
    
    gallery = gr.Gallery(
        label="Books", show_label=False, columns=3, height="auto"
    )
    
    search_box.change(search_books, inputs=search_box, outputs=gallery)
    
    # Initial load (empty query = show all)
    demo.load(search_books, inputs=search_box, outputs=gallery)

demo.launch()
