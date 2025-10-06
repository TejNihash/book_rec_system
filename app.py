import ast
import pandas as pd
import gradio as gr
import random
from datetime import datetime

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Enhanced data processing with error handling
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else ["Unknown Author"]))
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else ["Uncategorized"]))

# Add additional book metrics for richer display
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12  # 2 rows × 6 columns

# ---------- Enhanced Helpers ----------
def create_book_card_html(book):
    # Generate star rating display
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    
    # Truncate long descriptions
    description = book.get('description', 'No description available.')
    if len(description) > 300:
        description = description[:297] + "..."
    
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

def get_book_stats(books_df):
    """Generate statistics about the current book collection"""
    total_books = len(books_df)
    total_authors = len(set(author for authors in books_df['authors'] for author in authors))
    total_genres = len(set(genre for genres in books_df['genres'] for genre in genres))
    avg_rating = books_df['rating'].mean() if 'rating' in books_df.columns else 0
    return total_books, total_authors, total_genres, avg_rating

# ---------- Enhanced Gradio UI ----------
with gr.Blocks(css="""
.books-section {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    max-height: 600px;
    overflow-y: auto;
    margin-bottom: 15px;
    background: linear-gradient(135deg, #f7f7f7 0%, #ffffff 100%);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.books-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    margin-top: 15px;
}
.book-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.15);
    cursor: pointer;
    text-align: left;
    transition: all 0.3s ease;
    border: 1px solid #eaeaea;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.book-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    border-color: #667eea;
}
.book-image-container {
    position: relative;
    margin-bottom: 10px;
}
.book-card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #eee;
}
.book-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(102, 126, 234, 0.9);
    color: white;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: bold;
}
.book-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.book-title { 
    font-size: 13px; 
    font-weight: 700; 
    color: #222; 
    line-height: 1.3;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-bottom: 2px;
}
.book-authors { 
    font-size: 11px; 
    color: #667eea; 
    font-weight: 600;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    margin-bottom: 3px;
}
.book-rating {
    font-size: 10px;
    color: #ffa500;
    margin-bottom: 4px;
}
.book-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: auto;
}
.book-pages {
    font-size: 10px;
    color: #666;
    font-weight: 500;
}
.book-genres {
    font-size: 9px;
    color: #888;
    font-style: italic;
}
.stats-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 15px 0;
}
.stat-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 3px 8px rgba(0,0,0,0.2);
}
.stat-number {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 4px;
}
.stat-label {
    font-size: 11px;
    opacity: 0.9;
}
.load-more-section {
    text-align: center;
    margin: 20px 0;
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
}
.load-more-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
#detail-overlay { 
    display:none; 
    position:fixed; 
    top:0; 
    left:0; 
    width:100%; 
    height:100%; 
    background:rgba(0,0,0,0.85); 
    z-index:1000; 
    backdrop-filter: blur(5px);
}
#detail-box { 
    position:absolute; 
    background:#fff; 
    border-radius:16px; 
    padding:24px; 
    max-width:700px; 
    max-height:80vh;
    overflow-y: auto;
    box-shadow:0 12px 40px rgba(0,0,0,0.5); 
    color:#111; 
    border: 2px solid #667eea;
}
#detail-close { 
    position:absolute; 
    top:12px; 
    right:16px; 
    cursor:pointer; 
    font-size:24px; 
    font-weight:bold; 
    color: #667eea;
    background: white;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
#detail-content { 
    line-height:1.6; 
    font-size:15px; 
    color:#222; 
}
.detail-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 15px 0;
    padding: 12px;
    background: #f8f9ff;
    border-radius: 8px;
    border: 1px solid #e0e6ff;
}
.detail-stat {
    text-align: center;
}
.detail-stat-value {
    font-size: 16px;
    font-weight: bold;
    color: #667eea;
}
.detail-stat-label {
    font-size: 11px;
    color: #666;
    margin-top: 2px;
}
""") as demo:

    gr.Markdown("# 📚 Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # Stats display
    stats_html = gr.HTML()

    # Random Books State
    loaded_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    display_books_state = gr.State(pd.DataFrame())  # currently shown books
    load_index_state = gr.State(0)  # current "page" index

    books_container = gr.HTML()
    
    with gr.Row():
        load_more_btn = gr.Button("📚 Load More Books", elem_classes="load-more-btn")
        shuffle_btn = gr.Button("🔀 Shuffle Books")

    # ---------- Enhanced Functions ----------
    def update_stats(books_df):
        total_books, total_authors, total_genres, avg_rating = get_book_stats(books_df)
        stats_html = f"""
        <div class='stats-container'>
            <div class='stat-box'>
                <div class='stat-number'>{total_books}</div>
                <div class='stat-label'>Total Books</div>
            </div>
            <div class='stat-box'>
                <div class='stat-number'>{total_authors}</div>
                <div class='stat-label'>Unique Authors</div>
            </div>
            <div class='stat-box'>
                <div class='stat-number'>{total_genres}</div>
                <div class='stat-label'>Book Genres</div>
            </div>
            <div class='stat-box'>
                <div class='stat-number'>{avg_rating:.1f}</div>
                <div class='stat-label'>Avg Rating</div>
            </div>
        </div>
        """
        return stats_html

    def load_more(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    def shuffle_books(loaded_books, display_books):
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        stats = update_stats(initial_books)
        return shuffled, initial_books, html, stats, 1

    # Event handlers
    load_more_btn.click(
        load_more,
        [loaded_books_state, display_books_state, load_index_state],
        [display_books_state, books_container, load_more_btn, load_index_state]
    )

    shuffle_btn.click(
        shuffle_books,
        [loaded_books_state, display_books_state],
        [loaded_books_state, display_books_state, books_container, stats_html, load_index_state]
    )

    # Initialize first load
    def initial_load(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        stats = update_stats(initial_books)
        return initial_books, html, stats, 1

    display_books_state.value, books_container.value, stats_html.value, load_index_state.value = initial_load(loaded_books_state.value)

    # ---------- Enhanced Detail Popup ----------
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

    function escapeHtml(str){return str?String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'):"";}

    function formatText(text) {
        if (!text) return 'No description available.';
        // Simple paragraph formatting
        return text.replace(/\\n/g, '<br>').replace(/(.{80,}?)\\s/g, '$1 ');
    }

    document.addEventListener('click', e=>{
        const card = e.target.closest('.book-card');
        if(!card) return;
        
        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const genres = card.dataset.genres;
        const desc = card.dataset.desc;
        const img = card.dataset.img;
        const rating = card.dataset.rating || '0';
        const year = card.dataset.year || 'N/A';
        const pages = card.dataset.pages || 'N/A';
        
        // Generate star rating
        const numRating = parseFloat(rating);
        const fullStars = Math.floor(numRating);
        const hasHalfStar = numRating % 1 >= 0.5;
        let stars = '⭐'.repeat(fullStars);
        if (hasHalfStar) stars += '½';
        stars += '☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0));
        
        document.getElementById('detail-content').innerHTML = `
            <div style="display:flex;gap:20px;align-items:flex-start;margin-bottom:20px;">
                <img src="${img}" style="width:200px;height:auto;border-radius:8px;object-fit:cover;box-shadow:0 4px 12px rgba(0,0,0,0.3);">
                <div style="flex:1; color:#111;">
                    <h2 style="margin:0 0 12px 0;color:#2d3748;border-bottom:2px solid #667eea;padding-bottom:8px;">${escapeHtml(title)}</h2>
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
                    <div class="detail-stat-value">${Math.ceil(parseInt(pages) / 250) || 'N/A'}</div>
                    <div class="detail-stat-label">READING TIME (HOURS)</div>
                </div>
            </div>
            <div style="margin-top:15px;">
                <h3 style="margin:0 0 10px 0;color:#2d3748;font-size:16px;">Description</h3>
                <div style="background:#f8f9ff;padding:15px;border-radius:8px;border-left:4px solid #667eea;font-size:14px;line-height:1.6;">
                    ${formatText(escapeHtml(desc))}
                </div>
            </div>
        `;
        
        // Center the popup
        box.style.left = '50%';
        box.style.top = '50%';
        box.style.transform = 'translate(-50%, -50%)';
        overlay.style.display = 'block';
    });

    closeBtn.addEventListener('click', ()=>{overlay.style.display='none';});
    overlay.addEventListener('click', e=>{if(e.target===overlay) overlay.style.display='none';});
    document.addEventListener('keydown', e=>{if(e.key==='Escape') overlay.style.display='none';});
    </script>
    """)

    gr.Markdown("---")
    gr.Markdown("<div style='text-align: center; color: #666; font-size: 12px;'>📖 Keep exploring! There's always another great book waiting to be discovered.</div>")

demo.launch()