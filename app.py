import pandas as pd
import gradio as gr
import random
import ast

# ======= Load dataset =======
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12
favorites_list = []

# ======= Helper Functions =======
def create_book_card_html(book):
    """Return minimal HTML for a book card (clickable)."""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    return f"""
    <div class='book-card' data-id='{book["id"]}'>
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'" style="width:120px;height:180px;object-fit:cover;">
        <div style="color:#eee;font-size:12px;margin-top:4px;">{book['title']}</div>
        <div style="color:#aaa;font-size:11px;">{', '.join(book['authors'])}</div>
        <div style="color:#ffa500;font-size:11px;">{stars}</div>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div style='color:#888;'>No books available.</div>"
    return "<div style='display:flex;flex-wrap:wrap;gap:12px;'>" + "".join([create_book_card_html(b) for _, b in books_df.iterrows()]) + "</div>"

def get_book_details(book_id):
    """Return HTML for details and add-to-fav button."""
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return "<div>No book found.</div>", None
    book = book_match.iloc[0].to_dict()
    rating = book.get("rating",0)
    stars = "⭐" * int(rating) + "☆" * (5-int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4-int(rating))
    
    html = f"""
    <img src="{book['image_url']}" style="width:150px;height:220px;object-fit:cover;float:left;margin-right:12px;">
    <div style="color:#eee;font-size:14px;">
        <h3>{book['title']}</h3>
        <p><strong>Authors:</strong> {', '.join(book['authors'])}</p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p><strong>Year:</strong> {book.get('year','N/A')}</p>
        <p><strong>Pages:</strong> {book.get('pages','N/A')}</p>
        <p><strong>Rating:</strong> {stars} ({rating:.1f})</p>
        <p>{book.get('description','No description')}</p>
    </div>
    """
    return html, book['id']

def add_to_favorites(book_id):
    global favorites_list
    book_match = df[df['id']==book_id]
    if book_match.empty:
        return gr.update(value="❌ Book not found."), build_books_grid_html(pd.DataFrame(favorites_list))
    book = book_match.iloc[0].to_dict()
    if any(f['id']==book_id for f in favorites_list):
        return gr.update(value="⚠️ Already in favorites!"), build_books_grid_html(pd.DataFrame(favorites_list))
    favorites_list.append(book)
    return gr.update(value=f"❤️ Added '{book['title']}' to favorites!"), build_books_grid_html(pd.DataFrame(favorites_list))

# ======= Gradio UI =======
with gr.Blocks() as demo:
    gr.Markdown("# 📚 Dark Book Discovery Hub")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## 🎲 Random Books")
            random_books_container = gr.HTML(build_books_grid_html(df.sample(frac=1).reset_index(drop=True)))
            book_details_container = gr.HTML("<div style='color:#888;'>Click a book to see details here.</div>")
            add_fav_feedback = gr.Textbox(value="", interactive=False)
            add_fav_btn = gr.Button("❤️ Add to Favorites", visible=False)
            
        with gr.Column(scale=1):
            gr.Markdown("## ⭐ Favorites")
            favorites_container = gr.HTML("<div style='color:#888;'>No favorites yet.</div>")
    
    # ======= Events =======
    def on_card_click(evt: dict):
        book_id = evt['id']
        html, book_id_for_button = get_book_details(book_id)
        return html, gr.update(visible=True, interactive=True), book_id_for_button
    
    # JS click triggers card id
    random_books_container.js_on_event(
        "click",
        None,
        None,
        _js=f"""
        (evt) => {{
            const card = evt.target.closest('.book-card');
            if(card){{
                const book_id = card.dataset.id;
                const event = new CustomEvent('card_click', {{detail: {{id: book_id}}}});
                document.dispatchEvent(event);
            }}
        }}
        """
    )
    
    # Gradio listener for custom event
    book_details_state = gr.State()
    def handle_card_click(event_data):
        if event_data is None:
            return "<div>Click a book.</div>", gr.update(visible=False), None
        return on_card_click(event_data)
    
    book_details_container.change(
        handle_card_click,
        inputs=[book_details_state],
        outputs=[book_details_container, add_fav_btn, gr.State()]
    )
    
    add_fav_btn.click(
        add_to_favorites,
        inputs=[book_details_state],
        outputs=[add_fav_feedback, favorites_container]
    )

demo.launch()
