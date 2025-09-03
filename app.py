import gradio as gr
import pandas as pd
import ast

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, image_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Precompute lowercase for faster search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

def search_books(query):
    query = query.strip().lower()
    if query:
        mask_title = df["title_lower"].str.contains(query)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df
    
    gallery_data = []
    for _, row in filtered.iterrows():
        authors_str = ", ".join(row["authors"])
        genres_str = ", ".join(row["genres"])
        caption = f"**{row['title']}**\nby {authors_str}\n*{genres_str}*"
        gallery_data.append((row["image_url"], caption))
    
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
    
    # Initial load (show all books)
    demo.load(search_books, inputs=search_box, outputs=gallery)

demo.launch()
