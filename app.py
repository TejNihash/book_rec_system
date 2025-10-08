import pandas as pd
import random
import ast
import gradio as gr

# ====== Load Dataset ======
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


# ====== Helper Functions ======
def create_book_card_html(book, is_favorite=False):
    """Return a single book card HTML."""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))

    heart = "❤️" if is_favorite else "🤍"

    return f"""
    <div class='book-card' data-id='{book["id"]}'>
        <div class='heart' data-id='{book["id"]}'>{heart}</div>
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'">
        <div class='book-info'>
            <div class='title'>{book['title']}</div>
            <div class='authors'>{', '.join(book['authors'][:2])}</div>
            <div class='rating'>{stars}</div>
        </div>
    </div>
    """


def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div style='color:#888;'>No books found.</div>"
    cards = []
    for _, book in books_df.iterrows():
        is_fav = any(f['id'] == book['id'] for f in favorites_list)
        cards.append(create_book_card_html(book, is_fav))
    return f"<div class='books-grid'>{''.join(cards)}</div>"


def get_book_details_html(book_id):
    book_match = df[df["id"] == book_id]
    if book_match.empty:
        return "<div style='color:#aaa;'>No details found.</div>"
    b = book_match.iloc[0]
    stars = "⭐" * int(b.rating) + "☆" * (5 - int(b.rating))
    return f"""
    <div class='details'>
        <img src="{b['image_url']}" onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'">
        <div>
            <h3>{b['title']}</h3>
            <p><strong>Author(s):</strong> {', '.join(b['authors'])}</p>
            <p><strong>Genres:</strong> {', '.join(b['genres'])}</p>
            <p><strong>Year:</strong> {b['year']} | <strong>Pages:</strong> {b['pages']}</p>
            <p><strong>Rating:</strong> {stars} ({b['rating']:.1f})</p>
            <p class='desc'>{b.get('description', 'No description available.')}</p>
        </div>
    </div>
    """


def toggle_favorite(book_id):
    global favorites_list
    book_match = df[df["id"] == book_id]
    if book_match.empty:
        return build_books_grid_html(df.sample(BOOKS_PER_LOAD)), "<div>No details.</div>", build_books_grid_html(pd.DataFrame(favorites_list))
    book = book_match.iloc[0].to_dict()
    if any(f["id"] == book_id for f in favorites_list):
        favorites_list = [f for f in favorites_list if f["id"] != book_id]
    else:
        favorites_list.append(book)
    return (
        build_books_grid_html(df.sample(BOOKS_PER_LOAD)),
        get_book_details_html(book_id),
        build_books_grid_html(pd.DataFrame(favorites_list)),
    )


def show_details(book_id):
    return get_book_details_html(book_id)


# ====== UI ======
with gr.Blocks(css="""
.books-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
}
.book-card {
    position: relative;
    background: #333;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
    transition: transform 0.2s;
    cursor: pointer;
}
.book-card:hover {
    transform: translateY(-4px);
}
.book-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}
.book-info {
    padding: 8px;
    color: #eee;
    font-size: 12px;
}
.book-info .title {
    font-weight: bold;
    color: #fff;
    margin-bottom: 4px;
}
.heart {
    position: absolute;
    top: 6px;
    right: 8px;
    cursor: pointer;
    font-size: 16px;
}
.details {
    display: flex;
    gap: 12px;
    background: #222;
    padding: 12px;
    border-radius: 10px;
    color: #eee;
}
.details img {
    width: 150px;
    height: 220px;
    object-fit: cover;
    border-radius: 8px;
}
.details .desc {
    font-size: 13px;
    color: #ccc;
    max-height: 120px;
    overflow-y: auto;
}
""") as demo:
    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore books — click a card to view details, or tap the ❤️ to add to favorites.")

    random_books = gr.HTML(build_books_grid_html(df.sample(BOOKS_PER_LOAD)))
    details_box = gr.HTML("<div style='color:#888;'>Click a book to view details here.</div>")
    favorites_box = gr.HTML("<div style='color:#888;'>No favorites yet.</div>")

    hidden_toggle = gr.Button("toggle hidden", visible=False)
    hidden_input = gr.Textbox(visible=False)

    # Event wiring
    hidden_toggle.click(toggle_favorite, inputs=[hidden_input], outputs=[random_books, details_box, favorites_box])

    gr.HTML("""
<script>
document.addEventListener('click', (e) => {
    const heart = e.target.closest('.heart');
    const card = e.target.closest('.book-card');
    const input = document.querySelector('input[type="text"]');
    const hiddenButton = document.querySelector('button');
    if (heart) {
        input.value = heart.dataset.id;
        hiddenButton.click();
        e.stopPropagation();
        return;
    }
    if (card) {
        const id = card.dataset.id;
        const detailBox = document.querySelector('[data-testid="component-html"] + div > div'); 
        if (id && window.parent) {
            window.parent.postMessage({type: 'book_click', id: id}, '*');
        }
    }
});
</script>
""")

demo.launch()
