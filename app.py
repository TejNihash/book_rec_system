import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12  # 2 rows × 6 books

# ---------- Helper functions ----------
def create_book_card_html(book):
    return f"""
    <div class="book-card" onclick="selectBook('{book['id']}')">
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-title">{book['title']}</div>
        <div class="book-authors">by {', '.join(book['authors'])}</div>
        <div class="book-genres">{', '.join(book['genres'][:2])}</div>
    </div>
    """

def create_books_grid_html(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    return f"<div class='book-grid'>{''.join([create_book_card_html(row) for _, row in books_df.iterrows()])}</div>"

def get_book_details_html(book_id):
    book = df[df["id"] == book_id].iloc[0]
    return f"""
    <div style="padding:20px; max-width:600px; color:#000; background:white; border-radius:8px; 
                box-shadow:0 4px 16px rgba(0,0,0,0.2);">
        <img src="{book['image_url']}" style="width:150px; float:left; margin-right:20px;" 
             onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <h2>{book['title']}</h2>
        <p><strong>Author(s):</strong> {', '.join(book['authors'])}</p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p><strong>Published:</strong> {book.get('published_year', 'Unknown')}</p>
        <p><strong>Rating:</strong> {book.get('average_rating', 'Not rated')}</p>
        <p><strong>Pages:</strong> {book.get('num_pages', 'Unknown')}</p>
        <p>{book.get('description', 'No description available.')}</p>
        <button onclick="document.getElementById('detail-overlay').style.display='none';" 
                style="margin-top:10px;">Close</button>
    </div>
    """

def load_books(page=0):
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    return df.sample(frac=1).reset_index(drop=True).iloc[start_idx:end_idx]

# ---------- Gradio App ----------
with gr.Blocks(css="""
.book-grid {
    display:grid; grid-template-columns: repeat(6, 1fr); gap:10px; 
}
.book-card {
    cursor:pointer; padding:10px; background:white; border-radius:6px; 
    box-shadow:0 2px 8px rgba(0,0,0,0.1); text-align:center; transition:0.2s;
}
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:4px; }
.book-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.15); }
.book-title { font-weight:bold; font-size:12px; margin:4px 0; }
.book-authors { font-size:10px; color:#555; }
.book-genres { font-size:9px; font-style:italic; color:#777; }
.section-container { max-height:500px; overflow-y:auto; padding:10px; background:#fafafa; border-radius:8px; border:1px solid #ccc; margin-bottom:20px;}
.load-more-btn { margin:10px auto; display:flex; justify-content:center; }
.detail-overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:none; align-items:center; justify-content:center; z-index:1000; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # ---------- Random Books Section ----------
    gr.Markdown("🎲 Random Books")
    random_display = gr.HTML()
    load_random_btn = gr.Button("📚 Load More Books", elem_classes="load-more-btn")

    # ---------- Detail overlay ----------
    detail_overlay = gr.HTML("<div id='detail-overlay' class='detail-overlay'></div>")

    # ---------- States ----------
    random_page_state = gr.State(0)
    random_books_state = gr.State(load_books(0))

    # ---------- Callbacks ----------
    def show_random_books(page, current_books):
        new_books = load_books(page)
        combined = pd.concat([current_books, new_books], ignore_index=True)
        return create_books_grid_html(combined), page+1, combined

    def show_details(book_id):
        return f"<div class='detail-content'>{get_book_details_html(book_id)}</div>" + \
               "<script>document.getElementById('detail-overlay').style.display='flex';</script>"

    def hide_details():
        return "<div></div><script>document.getElementById('detail-overlay').style.display='none';</script>"

    # ---------- Events ----------
    load_random_btn.click(
        show_random_books,
        inputs=[random_page_state, random_books_state],
        outputs=[random_display, random_page_state, random_books_state]
    )

    # ---------- JS for card clicks ----------
    gr.HTML("""
    <script>
    function selectBook(bookId){
        gradioApp().getComponent('detail_overlay').setValue(bookId);
    }
    document.addEventListener('keydown', function(event){
        if(event.key==='Escape'){document.getElementById('detail-overlay').style.display='none';}
    });
    </script>
    """)

    # ---------- Detail overlay interaction ----------
    detail_overlay.change(
        show_details,
        inputs=[detail_overlay],
        outputs=[detail_overlay]
    )

    # ---------- Initial load ----------
    def initial_load(random_books_state=random_books_state):
        return create_books_grid_html(random_books_state.value)

    demo.load(
        initial_load,
        inputs=None,
        outputs=random_display
    )

demo.launch()
