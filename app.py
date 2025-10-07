import gradio as gr
import pandas as pd

# Mock data for demo
df = pd.DataFrame([
    {"id": "1", "title": "Dune", "author": "Frank Herbert"},
    {"id": "2", "title": "1984", "author": "George Orwell"},
    {"id": "3", "title": "Foundation", "author": "Isaac Asimov"},
])

# State
favorites_state = gr.State([])
current_book_id = gr.State(None)

def show_details(book_id):
    """Return popup HTML for a book + update current_book_id"""
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div class='popup'>
        <h2>{book.title}</h2>
        <p>Author: {book.author}</p>
        <button id='fav-btn' style='padding:8px 16px; background:#333; color:white; border:none; border-radius:4px; cursor:pointer;'>Add to Favorites</button>
        <script>
        document.getElementById('fav-btn').onclick = () => {{
            window.parent.postMessage({{"type":"add_fav_click"}}, "*");
        }};
        </script>
    </div>
    """
    return html, book_id

def add_to_favorites(book_id, favorites):
    """Adds the book to favorites if not already there"""
    if not book_id:
        return favorites, gr.update(value="<p>No book selected</p>")
    if book_id not in favorites:
        favorites.append(book_id)
    fav_html = render_favorites(favorites)
    return favorites, fav_html

def render_favorites(fav_ids):
    """Render the favorites section"""
    if not fav_ids:
        return "<p>No favorites yet.</p>"
    favs = df[df["id"].isin(fav_ids)]
    html = "<h3>⭐ Favorites</h3><ul>"
    for _, row in favs.iterrows():
        html += f"<li><b>{row.title}</b> by {row.author}</li>"
    html += "</ul>"
    return html

with gr.Blocks() as demo:
    gr.Markdown("## 📚 Book List + Favorites Demo")

    favorites_box = gr.HTML(render_favorites([]))

    with gr.Row():
        for _, row in df.iterrows():
            with gr.Column():
                gr.HTML(f"<div class='book-card' style='border:1px solid #ccc; padding:10px; border-radius:8px; cursor:pointer;' id='book-{row.id}'>{row.title}<br><small>{row.author}</small></div>")
                view_btn = gr.Button(f"View Details ({row.title})", elem_id=f"view-{row.id}")
                view_btn.click(show_details, inputs=[gr.Textbox(value=row.id, visible=False)], outputs=[gr.HTML(), current_book_id])

    fav_btn = gr.Button("❤️ Add to Favorites", visible=True)
    fav_btn.click(add_to_favorites, inputs=[current_book_id, favorites_state], outputs=[favorites_state, favorites_box])

demo.launch()
