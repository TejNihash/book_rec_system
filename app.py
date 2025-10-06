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

BOOKS_PER_LOAD = 12  # 2 rows x 6 books

# ---------- Helper Functions ----------
def create_book_card(book):
    """Collapsed book card with cover"""
    return f"""
    <div class='book-card' data-id='{book['id']}'>
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-title">{book['title']}</div>
        <div class="book-authors">by {', '.join(book['authors'])}</div>
    </div>
    """

def create_books_grid(books_df):
    """Generate grid HTML for a dataframe of books"""
    if books_df.empty:
        return "<div style='padding:30px;text-align:center;color:#666;'>No books found</div>"
    cards_html = "".join([create_book_card(row) for _, row in books_df.iterrows()])
    return f"<div class='books-grid'>{cards_html}</div>"

def get_book_details(book_id):
    book = df[df["id"]==book_id].iloc[0]
    return f"""
    <div id='detail-content'>
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:6px;float:left;margin-right:12px;">
        <h2>{book['title']}</h2>
        <p><strong>Authors:</strong> {', '.join(book['authors'])}</p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p><strong>Pages:</strong> {book.get('num_pages', 'Unknown')}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """

def load_more(current_books, all_books, page_idx):
    start = page_idx * BOOKS_PER_LOAD
    end = start + BOOKS_PER_LOAD
    new_books = all_books.iloc[start:end]
    combined = pd.concat([current_books, new_books], ignore_index=True)
    html = create_books_grid(combined)
    return html, combined, page_idx + 1

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section {
    border:1px solid #ccc; padding:12px; border-radius:10px; max-height:520px; overflow-y:auto; margin-bottom:20px;
    background:#f7f7f7;
}
.books-grid {
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap:12px;
}
.book-card {
    background:white; border-radius:8px; padding:8px; text-align:center; cursor:pointer; transition:all 0.3s;
}
.book-card:hover {
    transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,0.2);
}
.book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
.book-title { font-weight:bold; font-size:12px; color:#222; line-height:1.2; }
.book-authors { font-size:10px; color:#555; }
#detail-box { 
    position:absolute; background:white; color:#111; padding:16px; border-radius:8px; max-width:600px; 
    box-shadow:0 8px 20px rgba(0,0,0,0.35); z-index:9999;
}
#detail-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:999; display:none; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # ---------- Random Books Section ----------
    gr.Markdown("🎲 Random Books")
    random_section = gr.Column(elem_classes="books-section")
    random_display = gr.HTML()
    load_random_btn = gr.Button("📚 Load More Books")
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_page_state = gr.State(0)
    random_loaded_state = gr.State(pd.DataFrame())

    # ---------- Popular Books Section ----------
    gr.Markdown("📚 Popular Books")
    popular_section = gr.Column(elem_classes="books-section")
    popular_display = gr.HTML()
    load_popular_btn = gr.Button("📚 Load More Books")
    popular_books_state = gr.State(df)  # top rows
    popular_page_state = gr.State(0)
    popular_loaded_state = gr.State(pd.DataFrame())

    # ---------- Detail popup ----------
    detail_overlay = gr.HTML("<div id='detail-overlay'></div>")
    detail_box = gr.HTML("<div id='detail-box'></div>")

    # ---------- Event handlers ----------
    def show_book_details(book_id):
        html = get_book_details(book_id)
        return gr.update(value=html), gr.update(value="<script>document.getElementById('detail-overlay').style.display='block';</script>")

    def hide_details():
        return gr.update(value=""), gr.update(value="<script>document.getElementById('detail-overlay').style.display='none';</script>")

    def load_more_random(current_books, all_books, page_idx):
        html, combined, next_page = load_more(current_books, all_books, page_idx)
        return gr.update(value=html), combined, next_page

    def load_more_popular(current_books, all_books, page_idx):
        html, combined, next_page = load_more(current_books, all_books, page_idx)
        return gr.update(value=html), combined, next_page

    # ---------- JS for clicking cards ----------
    demo.load(
        None, None, None,
        js="""
        document.addEventListener('click', function(e){
            if(e.target.closest('.book-card')){
                const card = e.target.closest('.book-card');
                const bookId = card.dataset.id;
                card.dispatchEvent(new CustomEvent('book_click', {detail: bookId, bubbles:true}));
            }
        });
        document.addEventListener('keydown', function(e){
            if(e.key==='Escape'){
                document.getElementById('detail-box').innerHTML='';
                document.getElementById('detail-overlay').style.display='none';
            }
        });
        """
    )

    # ---------- Connect card clicks ----------
    random_display.js_on_event("book_click", show_book_details, outputs=[detail_box, detail_overlay])
    popular_display.js_on_event("book_click", show_book_details, outputs=[detail_box, detail_overlay])
    detail_overlay.click(fn=hide_details, outputs=[detail_box, detail_overlay])

    # ---------- Load initial ----------
    def init_random():
        html, combined, page_idx = load_more(pd.DataFrame(), random_books_state.value, 0)
        return gr.update(value=html), combined, page_idx
    def init_popular():
        html, combined, page_idx = load_more(pd.DataFrame(), popular_books_state.value, 0)
        return gr.update(value=html), combined, page_idx

    random_display.update, random_loaded_state.value, random_page_state.value = init_random()
    popular_display.update, popular_loaded_state.value, popular_page_state.value = init_popular()

    load_random_btn.click(load_more_random, [random_loaded_state, random_books_state, random_page_state],
                          [random_display, random_loaded_state, random_page_state])
    load_popular_btn.click(load_more_popular, [popular_loaded_state, popular_books_state, popular_page_state],
                           [popular_display, popular_loaded_state, popular_page_state])

demo.launch()
