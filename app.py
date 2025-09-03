import gradio as gr
import pandas as pd
import ast

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # title, authors, genres, img_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

def display_books(genre_filter):
    # Filter by genre if selected
    if genre_filter and genre_filter != "All":
        filtered = df[df["genres"].apply(lambda gs: genre_filter in gs)]
    else:
        filtered = df
    
    # Build gallery items
    gallery_data = []
    for _, row in filtered.iterrows():
        authors_str = ", ".join(row["authors"])
        genres_str = ", ".join(row["genres"])
        caption = f"**{row['title']}**\nby {authors_str}\n*{genres_str}*"
        gallery_data.append([row["img_url"], caption])
    
    return gallery_data

# Collect unique genres for dropdown
all_genres = sorted({g for gs in df["genres"] for g in gs})

with gr.Blocks() as demo:
    gr.Markdown("# 📚 My Book Showcase")
    
    with gr.Row():
        genre_dropdown = gr.Dropdown(
            ["All"] + all_genres,
            label="Filter by Genre",
            value="All"
        )
    
    gallery = gr.Gallery(
        label="Books", show_label=False, columns=3, height="auto"
    )
    
    genre_dropdown.change(display_books, inputs=genre_dropdown, outputs=gallery)
    
    # Initial load
    demo.load(display_books, inputs=genre_dropdown, outputs=gallery)

demo.launch()
