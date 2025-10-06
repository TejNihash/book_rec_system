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

BOOKS_PER_LOAD = 12  # 6 rows * 2 columns

# ---------- Helper functions ----------
def create_book_card(book, expanded=False):
    """Return HTML for a single book card, expanded or collapsed."""
    if expanded:
        return f"""
        <div class="book-card expanded" data-id="{book['id']}">
            <img src="{book['image_url']}" style="width:100%;height:auto;margin-bottom:10px;">
            <div class="book-info">
                <h3>{book['title']}</h3>
                <p><em>{', '.join(book['authors'])}</em></p>
                <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
                <p>{book.get('description','No description available.')}</p>
                <button class="collapse-btn">Collapse</button>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="book-card" data-id="{book['id']}">
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220?text=No+Image'">
            <div class="book-info">
                <div class="title">{book['title']}</div>
                <div class="authors">{', '.join(book['authors'])}</div>
                <div class="genres">{', '.join(book['genres'][:2])}</div>
            </div>
        </div>
        """

def create_books_grid_html(books_df):
    if books_df.empty:
        return '<div class="no-books">No books found</div>'
    return "".join([create_book_card(row) for _, row in books_df.iterrows()])

def expand_book(book_id, displayed_books_df):
    """Expand clicked book inline"""
    new_html = ""
    for _, book in displayed_books_df.iterrows():
        if book["id"] == book_id:
            new_html += create_book_card(book, expanded=True)
        else:
            new_html += create_book_card(book, expanded=False)
    return gr.update(value=new_html)

def collapse_all(displayed_books_df):
    """Collapse all expanded books"""
    new_html = "".join([create_book_card(row, expanded=False) for _, row in displayed_books_df.iterrows()])
    return gr.update(value=new_html)

def load_more_books(page, books_df, displayed_books_df):
    start = page*BOOKS_PER_LOAD
    end = start+BOOKS_PER_LOAD
    new_books = books_df.iloc[start:end]
    combined_books = pd.concat([displayed_books_df, new_books], ignore_index=True)
    html = create_books_grid_html(combined_books)
    return gr.update(value=html), page+1, combined_books

# ---------- CSS ----------
css = """
.container { border:1px solid #e0e0e0; border-radius:12px; padding:20px; margin:20px 0; 
    background:white; box-shadow:0 2px 8px rgba(0,0,0,0.1);}
.books-container { display:grid; grid-template-columns:repeat(2,1fr); gap:15px; 
    max-height:500px; overflow-y:auto; padding:10px; }
.book-card { background:white; border-radius:8px; padding:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); 
    display:flex; flex-direction:column; cursor:pointer; transition:all 0.3s ease; height:280px;}
.book-card.expanded { grid-column: span 2; height:auto; }
.book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:8px; }
.book-info { flex:1; display:flex; flex-direction:column; justify-content:space-between; }
.title { font-weight:bold; font-size:12px; color:black; overflow:hidden; display:-webkit-box; 
    -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.authors { font-size:10px; color:black; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; }
.genres { font-size:9px; color:black; font-style:italic; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; }
.load-more-btn { display:flex; justify-content:center; margin-top:10px; }
.collapse-btn { margin-top:10px; cursor:pointer; }
.no-books { text-align:center; padding:40px; font-style:italic; color:#666; }
"""

# ---------- Gradio App ----------
with gr.Blocks(css=css) as demo:
    gr.Markdown("# 📚 Book Explorer")

    # ---------- Random Books Section ----------
    with gr.Column(elem_classes="container"):
        gr.Markdown("🎲 Random Books")
        random_display = gr.HTML()
        load_random_btn = gr.Button("📚 Load More Random")
        random_page = gr.State(0)
        random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
        random_displayed_books = gr.State(pd.DataFrame())

    # ---------- Popular Books Section ----------
    with gr.Column(elem_classes="container"):
        gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML()
        load_popular_btn = gr.Button("📚 Load More Popular")
        popular_page = gr.State(0)
        popular_books_state = gr.State(df.copy())
        popular_displayed_books = gr.State(pd.DataFrame())

    # ---------- Load More Callbacks ----------
    load_random_btn.click(load_more_books,
                          inputs=[random_page, random_books_state, random_displayed_books],
                          outputs=[random_display, random_page, random_displayed_books])

    load_popular_btn.click(load_more_books,
                           inputs=[popular_page, popular_books_state, popular_displayed_books],
                           outputs=[popular_display, popular_page, popular_displayed_books])

    # ---------- Card click handler (JS) ----------
    js_click_handler = """
    <script>
    document.addEventListener('click', function(e){
        let card = e.target.closest('.book-card');
        if(card && !card.classList.contains('expanded')){
            let book_id = card.getAttribute('data-id');
            if(book_id){
                window._book_id = book_id;
                document.dispatchEvent(new CustomEvent("book_click"));
            }
        }
        if(e.target.classList.contains('collapse-btn')){
            document.dispatchEvent(new CustomEvent("book_collapse"));
        }
    });
    document.addEventListener("keydown", function(e){
        if(e.key === "Escape"){
            document.dispatchEvent(new CustomEvent("book_collapse"));
        }
    });
    </script>
    """
    gr.HTML(js_click_handler)

    # Hidden input for Python to know which book to expand
    book_id_input = gr.Textbox(value="", visible=False)

    # Expand/collapse callbacks
    random_display.change(expand_book,
                          inputs=[book_id_input, random_displayed_books],
                          outputs=random_display)
    random_display.change(collapse_all,
                          inputs=[random_displayed_books],
                          outputs=random_display)

    popular_display.change(expand_book,
                           inputs=[book_id_input, popular_displayed_books],
                           outputs=popular_display)
    popular_display.change(collapse_all,
                           inputs=[popular_displayed_books],
                           outputs=popular_display)

demo.launch()
