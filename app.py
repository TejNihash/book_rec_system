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
favorites_list = []

# ---------- Helpers ----------
def create_book_card_html(book):
    return f"""
    <div class='book-card' data-id='{book["id"]}'>
        <img src="{book['image_url']}" style="width:100%; height:180px; object-fit:cover; border-radius:8px;">
        <div style="margin-top:8px; font-weight:700; color:#fff;">{book['title']}</div>
        <div style="font-size:12px; color:#ccc;">by {', '.join(book['authors'])}</div>
    </div>
    """

def build_books_grid(df_):
    return "\n".join([create_book_card_html(book) for _, book in df_.iterrows()])

def show_book_details(book_id):
    book = df[df['id']==book_id].iloc[0]
    html = f"""
    <h3>{book['title']}</h3>
    <p><strong>Authors:</strong> {', '.join(book['authors'])}</p>
    <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
    <p><strong>Year:</strong> {book['year']}</p>
    <p><strong>Pages:</strong> {book['pages']}</p>
    """
    return html, gr.update(visible=True), book_id

def add_favorite(book_id):
    global favorites_list
    book = df[df['id']==book_id].iloc[0].to_dict()
    if all(fav['id'] != book_id for fav in favorites_list):
        favorites_list.append(book)
    favorites_html = build_books_grid(pd.DataFrame(favorites_list))
    return favorites_html

# ---------- Gradio UI ----------
with gr.Blocks() as demo:
    gr.Markdown("## Book Explorer")

    with gr.Row():
        # Books grid
        books_html = gr.HTML(value=build_books_grid(df.head(BOOKS_PER_LOAD)))
        # Favorites column
        favorites_html = gr.HTML(value="<p>No favorites yet.</p>")

    # Hidden state for currently selected book
    selected_book = gr.State()

    # Popup elements
    popup_html = gr.HTML(visible=False)
    add_fav_btn = gr.Button("❤️ Add to Favorites", visible=False)

    # ---------- Events ----------
    # Use JS to capture which book card is clicked
    books_html.click(
        fn=lambda x: None,
        inputs=[],
        outputs=[],
        _js="""
        () => {
            document.querySelectorAll('.book-card').forEach(card => {
                card.onclick = () => {
                    const bookId = card.dataset.id;
                    window._selectedBookId = bookId;
                    document.querySelector('.popup-container').style.display = 'block';
                    cardRect = card.getBoundingClientRect();
                    const popup = document.querySelector('.popup-container');
                    popup.style.top = (window.scrollY + cardRect.top) + 'px';
                    popup.style.left = (window.scrollX + cardRect.right + 10) + 'px';
                    gradioApp().getElementById('popup_html').setProps({value: bookId});
                }
            })
        }
        """
    )

    popup_html.change(show_book_details, inputs=[popup_html], outputs=[popup_html, add_fav_btn, selected_book])
    add_fav_btn.click(add_favorite, inputs=[selected_book], outputs=[favorites_html])

    # Popup container
    gr.HTML("""
    <div class="popup-container" style="display:none; position:absolute; background:#111; color:#eee; padding:16px; border-radius:12px; border:1px solid #667eea;">
        <span class="popup-close" onclick="this.parentElement.style.display='none'">&times;</span>
        <div id="popup_html"></div>
    </div>
    """)

demo.launch()
