import gradio as gr
import pandas as pd

# Load your dataset
df = pd.read_csv("data_mini_books.csv")  # assumes columns: title, authors, genres, img_url

def display_books(genre_filter):
    # Filter by genre if selected
    if genre_filter and genre_filter != "All":
        filtered = df[df['genres'].str.contains(genre_filter, case=False, na=False)]
    else:
        filtered = df
    
    # Build a list of [image, caption] pairs for Gradio Gallery
    gallery_data = []
    for _, row in filtered.iterrows():
        caption = f"**{row['title']}**\nby {row['authors']}\n*{row['genres']}*"
        gallery_data.append([row['img_url'], caption])
    
    return gallery_data

with gr.Blocks() as demo:
    gr.Markdown("# 📚 My Book Showcase")
    
    with gr.Row():
        genre_dropdown = gr.Dropdown(
            ["All"] + sorted(set(g for gs in df['genres'].dropna() for g in gs.split(","))),
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
