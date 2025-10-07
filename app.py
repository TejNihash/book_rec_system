import ast
import pandas as pd
import gradio as gr
import random

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# ---------- Favorites ----------
favorites_list = []

# ---------- Helpers ----------
def create_book_card(book, show_details=True):
    """Return HTML for a single book card with a Details button"""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    description = book.get("description", "No description available.")
    is_fav = any(f['id'] == book['id'] for f in favorites_list)
    fav_text = "❤️ " if is_fav else ""
    
    # Use Gradio Button instead of JS click
    details_btn = ""
    if show_details:
        details_btn = f"<button class='details-btn' data-id='{book['id']}' style='margin-top:6px;padding:4px 10px;border-radius:8px;border:none;background:#667eea;color:white;cursor:pointer;'>Details</button>"
    
    return f"""
    <div class='book-card' style='background:#333;border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:4px;color:#eee;'>
        <img src="{book['image_url']}" style="width:100%;height:180px;object-fit:cover;border-radius:8px;">
        <div style="font-weight:bold;">{fav_text}{book['title']}</div>
        <div style="font-size:12px;color:#88c;">by {', '.join(book['authors'])}</div>
        <div style="font-size:12px;color:#ffa500;">{stars} ({rating:.1f})</div>
        {details_btn}
    </div>
    """

def build_books_grid(books_df):
    html_cards = [create_book_card(row) for _, row in books_df.iterrows()]
    return "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;'>" + "".join(html_cards) + "</div>"

def update_favorites_html():
    if not favorites_list:
        return "<div style='color:#888;text-align:center;padding:20px;'>No favorite books yet.</div>"
    return "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;'>" + \
        "".join([create_book_card(fav, show_details=False) for fav in favorites_list]) + "</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.details-btn { cursor:pointer; background:#667eea; color:white; border:none; padding:6px 10px; border-radius:6px; }
.details-btn:hover { background:#5560c0; }
.favorite-btn { cursor:pointer; background:#ed8936; color:white; border:none; padding:8px 12px; border-radius:10px; font-weight:bold; }
.favorite-btn.remove { background:#f56565; }
""") as demo:

    gr.Markdown("# 📚 Book Recs Hub")
    
    # Random Books
    gr.Markdown("## 🎲 Random Books")
    random_books_html = gr.HTML()
    
    # Popular Books
    gr.Markdown("## 📈 Popular Books")
    popular_books_html = gr.HTML()
    
    # Favorites Section
    gr.Markdown("## ⭐ Favorites")
    favorites_html = gr.HTML(value=update_favorites_html())
    
    # Selected Book State
    selected_book_state = gr.State(None)
    
    # Popup
    popup_html = gr.HTML(value="", elem_id="popup", visible=False)
    
    # ---------- Functions ----------
    def load_random_books():
        books = df.sample(BOOKS_PER_LOAD)
        return build_books_grid(books)
    
    def load_popular_books():
        books = df.sample(BOOKS_PER_LOAD)  # For demo, random again
        return build_books_grid(books)
    
    def show_book_details(book_id):
        book = df[df['id']==book_id].iloc[0].to_dict()
        selected_book_state.value = book
        is_fav = any(f['id'] == book_id for f in favorites_list)
        btn_class = "favorite-btn remove" if is_fav else "favorite-btn"
        btn_text = "💔 Remove from Favorites" if is_fav else "❤️ Add to Favorites"
        html = f"""
        <div style='background:#111;padding:20px;border-radius:12px;color:#eee;max-width:600px;margin:20px auto;'>
            <h2>{book['title']}</h2>
            <div>Authors: {', '.join(book['authors'])}</div>
            <div>Genres: {', '.join(book['genres'])}</div>
            <div>Rating: {book.get('rating',0):.1f}</div>
            <div>Pages: {book.get('pages','N/A')}</div>
            <div style='margin-top:12px;'>{book.get('description','No description available.')}</div>
            <button class="{btn_class}" id="popup-fav-btn">{btn_text}</button>
        </div>
        """
        return gr.update(value=html, visible=True)
    
    def toggle_favorite(book):
        if book is None:
            return update_favorites_html(), None
        if any(f['id'] == book['id'] for f in favorites_list):
            favorites_list[:] = [f for f in favorites_list if f['id'] != book['id']]
        else:
            favorites_list.append(book)
        return update_favorites_html(), show_book_details(book['id'])
    
    # ---------- Initial Load ----------
    random_books_html.value = load_random_books()
    popular_books_html.value = load_popular_books()
    
    # ---------- Event Bindings ----------
    # Use JS to bind buttons to Gradio actions
    demo.load(
        lambda: None, [], [], _js="""
        // Bind Details buttons
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                const bookId = btn.getAttribute('data-id');
                window.gradioApp().getComponent('show_book_details').setValue(bookId);
            });
        });
        // Bind favorite button in popup
        document.addEventListener('click', e => {
            if(e.target.id==='popup-fav-btn'){
                window.gradioApp().getComponent('toggle_favorite').click();
            }
        });
        """
    )

demo.launch()
