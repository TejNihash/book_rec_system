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

# Add additional book metrics
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12  # 2 rows × 6 columns

# ---------- Helpers ----------
def create_book_card_html(book):
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    
    description = book.get('description', 'No description available.')
    
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{description}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{book['title']}</div>
            <div class='book-authors' title="{', '.join(book['authors'])}">by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres']) > 2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df):
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    height: 500px;
    overflow-y: auto;
    margin-bottom: 15px;
    background: linear-gradient(135deg, #f7f7f7 0%, #ffffff 100%);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.books-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
}
.load-more-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 25px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    margin: 10px 0;
}
#detail-overlay { 
    display:none; 
    position:fixed; 
    top:0; 
    left:0; 
    width:100%; 
    height:100%; 
    background:rgba(255,255,255,0.95);
    z-index:1000; 
    backdrop-filter: blur(5px);
}
#detail-box { 
    position:fixed; 
    top:50%; 
    left:50%; 
    transform: translate(-50%, -50%);
    background:#ffffff;
    border-radius:16px; 
    padding:24px; 
    max-width:700px; 
    max-height:80vh;
    overflow-y: auto;
    box-shadow:0 12px 40px rgba(0,0,0,0.3); 
    color:#222;
    border: 2px solid #667eea;
}
#detail-close { 
    position:absolute; 
    top:12px; 
    right:16px; 
    cursor:pointer; 
    font-size:24px; 
    font-weight:bold; 
    color: #222;
    background: #f0f0f0;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.description-scroll {
    max-height: 200px;
    overflow-y: auto;
    padding-right: 8px;
}
.description-scroll::-webkit-scrollbar {
    width: 6px;
}
.description-scroll::-webkit-scrollbar-thumb {
    background: #667eea;
    border-radius: 3px;
}
.description-scroll::-webkit-scrollbar-thumb:hover {
    background: #5a6fd8;
}
""") as demo:

    gr.Markdown("# 📚 Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # ---------- Random Books Section ----------
    gr.Markdown("## 🔀 Random Books")
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_load_index = gr.State(0)
    random_container = gr.HTML(elem_classes="books-section")
    with gr.Row():
        random_load_btn = gr.Button("📚 Load More Random", elem_classes="load-more-btn")

    # ---------- Popular Books Section ----------
    gr.Markdown("## ⭐ Popular Books")
    popular_books_state = gr.State(df.sort_values("rating", ascending=False).reset_index(drop=True))
    popular_display_state = gr.State(pd.DataFrame())
    popular_load_index = gr.State(0)
    popular_container = gr.HTML(elem_classes="books-section")
    with gr.Row():
        popular_load_btn = gr.Button("📚 Load More Popular", elem_classes="load-more-btn")

    # ---------- Functions ----------
    def load_more(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    # Initialize first load
    def initial_load(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    random_display_state.value, random_container.value, random_load_index.value = initial_load(random_books_state.value)
    popular_display_state.value, popular_container.value, popular_load_index.value = initial_load(popular_books_state.value)

    # ---------- Event Handlers ----------
    random_load_btn.click(
        load_more,
        [random_books_state, random_display_state, random_load_index],
        [random_display_state, random_container, random_load_btn, random_load_index]
    )
    popular_load_btn.click(
        load_more,
        [popular_books_state, popular_display_state, popular_load_index],
        [popular_display_state, popular_container, popular_load_btn, popular_load_index]
    )

    # ---------- Modal Popup ----------
    gr.HTML("""
    <div id="detail-overlay">
        <div id="detail-box">
            <span id="detail-close">&times;</span>
            <div id="detail-content"></div>
        </div>
    </div>
    <script>
    const overlay = document.getElementById('detail-overlay');
    const box = document.getElementById('detail-box');
    const closeBtn = document.getElementById('detail-close');
    let scrollPosition = 0;

    function escapeHtml(str){return str?String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'):"";}
    function formatText(text){return text?text.replace(/\\n/g,'<br>'):'No description available.';}

    document.addEventListener('click', e=>{
        const card = e.target.closest('.book-card');
        if(!card) return;

        scrollPosition = window.scrollY || document.documentElement.scrollTop;

        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const genres = card.dataset.genres;
        const desc = card.dataset.desc;
        const img = card.dataset.img;
        const rating = card.dataset.rating || '0';
        const year = card.dataset.year || 'N/A';
        const pages = card.dataset.pages || 'N/A';

        const numRating = parseFloat(rating);
        const fullStars = Math.floor(numRating);
        const hasHalfStar = numRating % 1 >= 0.5;
        let stars = '⭐'.repeat(fullStars);
        if(hasHalfStar) stars+='½';
        stars+='☆'.repeat(5-fullStars-(hasHalfStar?1:0));

        document.getElementById('detail-content').innerHTML = `
            <div style="display:flex;gap:20px;align-items:flex-start;margin-bottom:20px;">
                <img src="${img}" style="width:200px;height:auto;border-radius:8px;object-fit:cover;box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <div style="flex:1; color:#222;">
                    <h2 style="margin:0 0 12px 0;color:#1a202c;border-bottom:2px solid #667eea;padding-bottom:8px;">${escapeHtml(title)}</h2>
                    <p style="margin:0 0 8px 0;font-size:15px;"><strong>Author(s):</strong> <span style="color:#667eea;">${escapeHtml(authors)}</span></p>
                    <p style="margin:0 0 8px 0;font-size:15px;"><strong>Genres:</strong> <span style="color:#764ba2;">${escapeHtml(genres)}</span></p>
                    <p style="margin:0 0 8px 0;font-size:15px;"><strong>Rating:</strong> ${stars} <strong style="color:#667eea;">${parseFloat(rating).toFixed(1)}</strong></p>
                </div>
            </div>
            <div class="detail-stats">
                <div class="detail-stat">
                    <div class="detail-stat-value">${escapeHtml(year)}</div>
                    <div class="detail-stat-label">PUBLICATION YEAR</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${escapeHtml(pages)}</div>
                    <div class="detail-stat-label">PAGES</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${Math.ceil(parseInt(pages)/250)||'N/A'}</div>
                    <div class="detail-stat-label">READING TIME (HOURS)</div>
                </div>
            </div>
            <div style="margin-top:15px;">
                <h3 style="margin:0 0 10px 0;color:#1a202c;font-size:16px;">Description</h3>
                <div class="description-scroll" style="background:#f8f9ff;padding:15px;border-radius:8px;border-left:4px solid #667eea;font-size:14px;line-height:1.6;color:#222;">
                    ${formatText(escapeHtml(desc))}
                </div>
            </div>
        `;

        overlay.style.display='block';
        document.body.style.overflow='hidden';
    });

    function closePopup(){
        overlay.style.display='none';
        document.body.style.overflow='auto';
        window.scrollTo(0, scrollPosition);
    }

    closeBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', e=>{if(e.target===overlay)closePopup();});
    document.addEventListener('keydown', e=>{if(e.key==='Escape')closePopup();});
    </script>
    """)

demo.launch()
