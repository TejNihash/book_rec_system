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

BOOKS_PER_LOAD = 6

# ---------- Helper functions ----------
def create_book_card_html(book):
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
    cards_html = "".join([create_book_card_html(row) for _, row in books_df.iterrows()])
    return f'<div class="books-grid">{cards_html}</div>'

def show_book_modal(book_id):
    book = df[df["id"]==book_id].iloc[0]
    html = f"""
    <div class="modal-content">
        <img src="{book['image_url']}" style="width:200px;height:auto;border-radius:6px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <p><em>{', '.join(book['authors'])}</em></p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    return gr.update(visible=True), html

def load_more_books(page, books_df, displayed_books):
    start = page*BOOKS_PER_LOAD
    end = start+BOOKS_PER_LOAD
    new_books = books_df.iloc[start:end]
    combined_books = pd.concat([displayed_books, new_books], ignore_index=True)
    html = create_books_grid_html(combined_books)
    return gr.update(value=html), page+1, combined_books

# ---------- Gradio App ----------
with gr.Blocks(css="""
    .container { border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; margin: 20px 0;
        background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .books-container { max-height: 500px; overflow-y: auto; padding: 15px; background: #fafafa;
        border-radius: 8px; border: 1px solid #f0f0f0; margin-bottom: 15px; }
    .books-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }
    .book-card { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center; height: 280px; display: flex; flex-direction: column; transition: all 0.3s ease; cursor:pointer; }
    .book-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
    .book-card img { width: 100%; height: 160px; object-fit: cover; border-radius: 4px; margin-bottom: 8px; }
    .book-info { flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
    .title { font-weight: bold; font-size: 12px; line-height: 1.3; margin-bottom: 4px; color: #2c3e50;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .authors { font-size: 10px; color: #666; margin-bottom: 3px; display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden; }
    .genres { font-size: 9px; color: #888; font-style: italic; display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .section-title { font-size: 18px; font-weight: bold; color: #2c3e50; }
    .load-more-btn { display: flex; justify-content: center; margin-top: 10px; }
    .no-books { text-align: center; padding: 40px; color: #666; font-style: italic; }
    .modal-overlay { background: rgba(0,0,0,0.5); position: fixed; top:0; left:0; right:0; bottom:0;
        display:flex; align-items:center; justify-content:center; z-index:9999; }
    .modal-content { max-width: 800px; max-height: 80vh; overflow-y: auto; background:white; padding:20px; border-radius:10px; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # ---------- Random Section ----------
    with gr.Column(elem_classes="container"):
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("🎲 Random Books")
        random_display = gr.HTML()
        load_random_btn = gr.Button("📚 Load More Random")
        random_page = gr.State(0)
        random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
        random_displayed_books = gr.State(pd.DataFrame())

    # ---------- Popular Section ----------
    with gr.Column(elem_classes="container"):
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML()
        load_popular_btn = gr.Button("📚 Load More Popular")
        popular_page = gr.State(0)
        popular_books_state = gr.State(df.copy())
        popular_displayed_books = gr.State(pd.DataFrame())

    # ---------- Modal ----------
    book_modal = gr.Column(visible=False, elem_classes="modal-overlay")
    book_detail_html = gr.HTML()
    close_modal_btn = gr.Button("❌ Close")
    with book_modal:
        book_detail_html
        close_modal_btn
    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

    # ---------- Load More callbacks ----------
    load_random_btn.click(load_more_books,
                          inputs=[random_page, random_books_state, random_displayed_books],
                          outputs=[random_display, random_page, random_displayed_books])
    load_popular_btn.click(load_more_books,
                           inputs=[popular_page, popular_books_state, popular_displayed_books],
                           outputs=[popular_display, popular_page, popular_displayed_books])

    # ---------- Card click callback ----------
    def on_card_click(book_id):
        return show_book_modal(book_id)

    random_display.click(on_card_click, inputs=[gr.Textbox(value="")], outputs=[book_modal, book_detail_html])
    popular_display.click(on_card_click, inputs=[gr.Textbox(value="")], outputs=[book_modal, book_detail_html])

demo.launch()
