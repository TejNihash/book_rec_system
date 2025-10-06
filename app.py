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

BOOKS_PER_LOAD = 12  # 2 rows of 6 books

# ---------- Helpers ----------
def create_book_card(book):
    return f"""
    <div class='book-card' onclick="selectBook('{book['id']}')">
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-title">{book['title']}</div>
        <div class="book-authors">by {', '.join(book['authors'])}</div>
        <div class="book-genres">{', '.join(book['genres'][:2])}</div>
    </div>
    """

def create_books_grid_html(books_df):
    if books_df.empty:
        return "<div style='padding:20px;text-align:center;color:#666;'>No books found</div>"
    cards_html = "".join([create_book_card(row) for _, row in books_df.iterrows()])
    return f'<div class="book-grid">{cards_html}</div>'

def get_book_details(book_id):
    book = df[df["id"] == book_id].iloc[0]
    return f"""
    <div style="padding:20px;">
        <div style="display:flex; gap:20px; align-items:flex-start;">
            <img src="{book['image_url']}" style="width:200px; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.2);" 
                 onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
            <div>
                <h2 style="margin:0 0 10px 0; color:#111;">{book['title']}</h2>
                <p style="margin:5px 0; color:#333;"><strong>Author(s):</strong> {', '.join(book['authors'])}</p>
                <p style="margin:5px 0; color:#333;"><strong>Genres:</strong> {', '.join(book['genres'])}</p>
                <p style="margin:5px 0; color:#333;"><strong>Published:</strong> {book.get('published_year','Unknown')}</p>
                <p style="margin:5px 0; color:#333;"><strong>Rating:</strong> {book.get('average_rating','Not rated')}</p>
                <p style="margin:5px 0; color:#333;"><strong>Pages:</strong> {book.get('num_pages','Unknown')}</p>
                <div style="margin-top:20px;">
                    <h4 style="margin:0 0 10px 0; color:#111;">Description</h4>
                    <p style="line-height:1.6; color:#222;">{book.get('description','No description available.')}</p>
                </div>
            </div>
        </div>
    </div>
    """

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.book-section {
    border:1px solid #ddd; border-radius:12px; padding:15px; margin-bottom:20px; background:#fafafa;
    max-height:520px; overflow-y:auto;
}
.book-grid {
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap:15px;
}
.book-card {
    cursor:pointer; background:white; border-radius:8px; padding:8px;
    text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.1); transition: all 0.2s;
}
.book-card:hover { transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,0.15);}
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:4px; margin-bottom:6px;}
.book-title { font-weight:bold; font-size:12px; color:#111; margin-bottom:2px; }
.book-authors { font-size:10px; color:#555; margin-bottom:2px;}
.book-genres { font-size:9px; color:#777; font-style:italic; }
.modal-overlay { 
    position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); 
    display:none; justify-content:center; align-items:center; z-index:1000; 
}
.modal-content { background:white; padding:20px; border-radius:10px; max-width:800px; max-height:80vh; overflow-y:auto; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # Hidden state for selected book
    selected_book_id = gr.Textbox(visible=False, elem_id="selected-book-id")

    # ---------- Random Books ----------
    gr.Markdown("🎲 Random Books")
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_page_state = gr.State(0)
    random_display = gr.HTML()

    # Load More Button
    load_random_btn = gr.Button("📚 Load More")

    # ---------- Modal Overlay ----------
    detail_overlay = gr.HTML("""
    <div class="modal-overlay" id="book-modal">
        <div class="modal-content" id="modal-content"></div>
    </div>
    <script>
    function selectBook(bookId) {
        document.getElementById('selected-book-id').value = bookId;
        document.getElementById('selected-book-id').dispatchEvent(new Event('input',{bubbles:true}));
    }

    document.addEventListener('keydown', function(e){
        if(e.key==='Escape'){
            document.getElementById('book-modal').style.display='none';
        }
    });
    </script>
    """)

    # ---------- Python Functions ----------
    def load_random_books(random_books_df, page):
        start = page * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        page_books = random_books_df.iloc[start:end]
        html = create_books_grid_html(page_books)
        return html, page + 1

    def show_book_details(book_id):
        html = get_book_details(book_id)
        js = f"""
        <script>
            let overlay = document.getElementById('book-modal');
            let content = document.getElementById('modal-content');
            content.innerHTML = `{html}`;
            overlay.style.display = 'flex';
        </script>
        """
        return js

    # ---------- Event Bindings ----------
    load_random_btn.click(
        load_random_books,
        inputs=[random_books_state, random_page_state],
        outputs=[random_display, random_page_state]
    )

    selected_book_id.input(
        show_book_details,
        inputs=[selected_book_id],
        outputs=[detail_overlay]
    )

    # ---------- Initial Load ----------
    def initial_load():
        html, new_page = load_random_books(random_books_state.value, 0)
        random_page_state.value = new_page
        return html

    random_display.update(initial_load())

demo.launch()
