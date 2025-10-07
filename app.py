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

# ---------- Helpers ----------
def create_book_card_html(book, favorites_ids):
    is_fav = book["id"] in (favorites_ids or [])
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    description = book.get("description", "No description available.")
    fav_prefix = "❤️ " if is_fav else ""
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{description}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{fav_prefix}{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df, favorites_ids=None, is_favorites_section=False):
    favorites_ids = favorites_ids or []
    if books_df is None or (hasattr(books_df, "empty") and books_df.empty):
        if is_favorites_section:
            return "<div style='text-align:center;padding:40px;color:#888;font-size:16px;'>No favorite books yet. Click the ❤️ button in book details to add some!</div>"
        return "<div style='text-align:center;padding:40px;color:#888;'>No books found</div>"
    cards_html = []
    # If books_df is list of dicts convert to DataFrame
    if isinstance(books_df, list):
        books_df = pd.DataFrame(books_df)
    for _, book in books_df.iterrows():
        cards_html.append(create_book_card_html(book, favorites_ids))
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio App ----------
with gr.Blocks(css="""
/* styles (kept dark theme) */
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.18s ease; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 24px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:6px; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; }
.book-rating { font-size:10px; color:#ffa500; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }

/* buttons */
.load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 20px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.18s ease; box-shadow:0 4px 12px rgba(102,126,234,0.22); font-size:12px; }
.load-more-btn:hover { transform:translateY(-2px); }

/* popup overlay + container — container default is hidden and will be positioned near card */
.popup-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.45); backdrop-filter:blur(3px); z-index:99998; }
.popup-container { display:none; position:fixed; background:#111; color:#eee; border-radius:12px; padding:18px; width:320px; max-height:75vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.7); border:1px solid #333; z-index:99999; transform-origin: top left; }
.popup-close { position:absolute; top:8px; right:8px; cursor:pointer; font-size:20px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; }
.popup-close:hover { background:#667eea; color:white; }
.description-scroll { max-height:200px; overflow-y:auto; padding-right:8px; margin-top:10px; background:#222; border-radius:6px; padding:8px; border:1px solid #444; font-size:14px; line-height:1.5; }
.detail-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:12px 0; padding:12px; background:#1a1a1a; border-radius:8px; border:1px solid #333; }
.detail-stat { text-align:center; }
.detail-stat-value { font-size:16px; font-weight:bold; color:#667eea; }
.detail-stat-label { font-size:11px; color:#888; margin-top:4px; }
.favorite-action-section { margin-top:12px; }

/* favorites header count bubble */
.favorites-count { background:#ed8936; color:white; padding:4px 12px; border-radius:16px; font-size:12px; font-weight:600; margin-left:12px; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # ---------- Hidden Textbox (JS -> Python bridge) ----------
    favorite_book_id = gr.Textbox(visible=False, elem_id="fav-id")  # JS will set this and dispatch change

    # ---------- Favorites state & UI slots ----------
    favorites_state = gr.State([])  # list of favorite book ids
    favorites_header = gr.HTML("""
        <div style="display:flex; align-items:center; margin-bottom:12px;">
            <h2 style="margin:0; color:#fff; border-left:4px solid #ed8936; padding-left:10px;">⭐ Favorites</h2>
            <div class="favorites-count">0 books</div>
        </div>
    """)
    favorites_container = gr.HTML(elem_classes="books-section", value="<div style='text-align:center;padding:40px;color:#888;'>No favorite books yet.</div>")
    favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

    # ---------- Random / Popular containers ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
    shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    gr.Markdown("## 📈 Popular Books")
    popular_books_container = gr.HTML(elem_classes="books-section")
    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # ---------- States for pages ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)

    favorites_display_state = gr.State(pd.DataFrame())
    favorites_index_state = gr.State(0)

    # ---------- Python function to toggle favorite ---------- 
    def toggle_favorite_python(book_id, favorites_ids):
        """Add/remove book_id from favorites_ids and return updated UI pieces."""
        # defensive
        if not book_id:
            return favorites_ids or [], gr.update(value=build_books_grid_html(pd.DataFrame(), [])), gr.update(visible=False), gr.update(value="""
                <div style="display:flex; align-items:center; margin-bottom:12px;">
                    <h2 style="margin:0; color:#fff; border-left:4px solid #ed8936; padding-left:10px;">⭐ Favorites</h2>
                    <div class="favorites-count">0 books</div>
                </div>
            """)
        favorites_ids = list(favorites_ids or [])
        if book_id in favorites_ids:
            favorites_ids.remove(book_id)
        else:
            favorites_ids.append(book_id)

        fav_df = df[df['id'].isin(favorites_ids)].reset_index(drop=True)
        fav_html = build_books_grid_html(fav_df, favorites_ids, is_favorites_section=True)
        load_more_vis = len(favorites_ids) > BOOKS_PER_LOAD
        header_html = f"""
            <div style="display:flex; align-items:center; margin-bottom:12px;">
                <h2 style="margin:0; color:#fff; border-left:4px solid #ed8936; padding-left:10px;">⭐ Favorites</h2>
                <div class="favorites-count">{len(favorites_ids)} book{'s' if len(favorites_ids)!=1 else ''}</div>
            </div>
        """
        return favorites_ids, gr.update(value=fav_html), gr.update(visible=load_more_vis), gr.update(value=header_html)

    # Connect hidden textbox change to Python handler
    favorite_book_id.change(
        fn=toggle_favorite_python,
        inputs=[favorite_book_id, favorites_state],
        outputs=[favorites_state, favorites_container, favorites_load_more_btn, favorites_header]
    )

    # ---------- Loading / shuffle / more functions (unchanged logic) ----------
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books, favorites_state.value)
        return initial_books, html, 1

    def load_more(loaded, display, idx):
        start = idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded.iloc[start:end]
        if new_books.empty:
            return display, gr.update(value=build_books_grid_html(display, favorites_state.value)), gr.update(visible=False), idx
        combined = pd.concat([display, new_books], ignore_index=True)
        html = build_books_grid_html(combined, favorites_state.value)
        return combined, gr.update(value=html), gr.update(visible=True), idx + 1

    def shuffle_random(loaded, display):
        shuffled = loaded.sample(frac=1).reset_index(drop=True)
        initial = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial, favorites_state.value)
        return shuffled, initial, html, 1

    random_load_more_btn.click(load_more, [random_books_state, random_display_state, random_index_state],
                              [random_display_state, random_books_container, random_load_more_btn, random_index_state])
    shuffle_btn.click(shuffle_random, [random_books_state, random_display_state],
                      [random_books_state, random_display_state, random_books_container, random_index_state])
    popular_load_more_btn.click(load_more, [popular_books_state, popular_display_state, popular_index_state],
                                [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state])

    # ---------- Initial render ----------
    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load(popular_books_state.value)
    # favorites initially empty
    favorites_state.value = []
    favorites_container.value = "<div style='text-align:center;padding:40px;color:#888;'>No favorite books yet.</div>"

    # ---------- Popup HTML + JS (positions near card, uses hidden textbox) ----------
    gr.HTML("""
    <div class="popup-overlay" id="popup-overlay"></div>
    <div class="popup-container" id="popup-container" role="dialog" aria-modal="true">
        <span class="popup-close" id="popup-close">&times;</span>
        <div class="popup-content" id="popup-content"></div>
    </div>

    <script>
    (function(){
        const overlay = document.getElementById('popup-overlay');
        const container = document.getElementById('popup-container');
        const closeBtn = document.getElementById('popup-close');
        const content = document.getElementById('popup-content');

        // helper: escape HTML
        function escapeHtml(str){
            return str ? String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;') : '';
        }
        function formatText(text){
            if(!text) return 'No description available.';
            return text.replace(/\\n/g,'<br>');
        }

        let currentBookId = null;
        let originalScrollY = 0;

        function showFeedback(msg){
            const existing = document.querySelector('.favorite-feedback');
            if(existing) existing.remove();
            const el = document.createElement('div');
            el.className = 'favorite-feedback';
            el.style.cssText = 'position:fixed;top:18px;right:18px;background:#48bb78;color:#fff;padding:10px 14px;border-radius:8px;z-index:200000;font-weight:600;';
            el.textContent = msg;
            document.body.appendChild(el);
            setTimeout(()=>{ if(document.body.contains(el)) el.remove(); }, 1400);
        }
    
    function setHiddenFavoriteIdAndTrigger(bookId){
        // Get Gradio component wrapper
        const wrapper = (typeof gradioApp === 'function') ? gradioApp().getElementById('fav-id') : document.getElementById('fav-id');
        if(!wrapper){
            console.warn('⚠️ fav-id wrapper not found');
            return;
        }
    
        // Try to find the real <input> (different Gradio versions wrap it differently)
        let input = wrapper.querySelector('input, textarea');
        if(!input && wrapper.shadowRoot){
            input = wrapper.shadowRoot.querySelector('input, textarea');
        }
        if(!input){
            console.warn('⚠️ fav-id input not found');
            return;
        }
    
        // Set value and trigger events
        input.value = bookId;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    
        console.log("📤 Sent favorite ID to Python:", bookId);
    }

        function openPopupNearCard(card) {
            originalScrollY = window.scrollY || document.documentElement.scrollTop;
            currentBookId = card.dataset.id;

            const title = escapeHtml(card.dataset.title);
            const authors = escapeHtml(card.dataset.authors);
            const genres = escapeHtml(card.dataset.genres);
            const desc = escapeHtml(card.dataset.desc);
            const img = escapeHtml(card.dataset.img);
            const rating = card.dataset.rating || '0';
            const year = card.dataset.year || 'N/A';
            const pages = card.dataset.pages || 'N/A';

            const numRating = parseFloat(rating);
            const fullStars = Math.floor(numRating);
            const hasHalf = numRating % 1 >= 0.5;
            let stars = '⭐'.repeat(fullStars) + (hasHalf ? '½' : '') + '☆'.repeat(5 - fullStars - (hasHalf ? 1 : 0));

            content.innerHTML = `
                <div style="display:flex; gap:16px; align-items:flex-start;">
                    <img src="${img}" style="width:140px;height:auto;border-radius:8px;object-fit:cover;box-shadow:0 6px 18px rgba(0,0,0,0.5);">
                    <div style="flex:1;">
                        <h2 style="margin:0 0 8px 0;color:#fff;border-bottom:2px solid #667eea;padding-bottom:6px;">${title}</h2>
                        <p style="margin:6px 0;"><strong style="color:#88c">Author(s):</strong> <span style="color:#667eea">${authors}</span></p>
                        <p style="margin:6px 0;"><strong style="color:#88c">Genres:</strong> <span style="color:#a78bfa">${genres}</span></p>
                        <p style="margin:6px 0;"><strong style="color:#88c">Rating:</strong> ${stars} <strong style="color:#ffa500">${parseFloat(rating).toFixed(1)}</strong></p>
                        <div class="detail-stats">
                            <div class="detail-stat"><div class="detail-stat-value">${escapeHtml(year)}</div><div class="detail-stat-label">PUBLICATION YEAR</div></div>
                            <div class="detail-stat"><div class="detail-stat-value">${escapeHtml(pages)}</div><div class="detail-stat-label">PAGES</div></div>
                            <div class="detail-stat"><div class="detail-stat-value">${Math.ceil(parseInt(pages)/250) || 'N/A'}</div><div class="detail-stat-label">READING TIME (HOURS)</div></div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:12px;">
                    <h3 style="margin:0 0 8px 0;color:#fff;font-size:15px;">Description</h3>
                    <div class="description-scroll">${formatText(desc)}</div>
                </div>
                <div class="favorite-action-section">
                    <button class="favorite-btn" id="popup-fav-btn">❤️ Add to Favorites</button>
                </div>
            `;

            // position the container near the card (fixed relative to viewport)
            const rect = card.getBoundingClientRect();
            let top = rect.top;
            let left = rect.right + 12;

            // ensure it stays in viewport horizontally
            container.style.transform = 'none'; // remove centering transform
            container.style.position = 'fixed';

            // temporarily show container offscreen to compute width/height
            container.style.display = 'block';
            container.style.top = '-9999px';
            container.style.left = '-9999px';

            // compute offset and adjust
            const cw = container.offsetWidth;
            const ch = container.offsetHeight;
            if (left + cw > window.innerWidth) {
                left = rect.left - cw - 12;
                if (left < 8) left = 8; // fallback
            }
            if (top + ch > window.innerHeight) {
                top = Math.max(8, window.innerHeight - ch - 8);
            }
            container.style.top = `${top}px`;
            container.style.left = `${left}px`;

            // show overlay too
            overlay.style.display = 'block';
            container.style.display = 'block';
            // lock background scroll
            document.body.style.overflow = 'hidden';

            // Hook up popup favorite button
            const popupFavBtn = document.getElementById('popup-fav-btn');
            if (popupFavBtn) {
                popupFavBtn.onclick = function(){ 
                    // set hidden value and trigger python
                    setHiddenFavoriteIdAndTrigger(currentBookId);
                    showFeedback('Saved to favorites');
                    // small UI flip to indicate expected change
                    popupFavBtn.innerText = '✅ Saved';
                    setTimeout(()=>{ popupFavBtn.innerText = '❤️ Add to Favorites'; }, 900);
                };
            }
        }

        // Event delegation: catch clicks on dynamically generated .book-card
        document.addEventListener('click', function(e){
            const card = e.target.closest('.book-card');
            if (!card) return;
            openPopupNearCard(card);
        });

        function closePopup(){
            overlay.style.display = 'none';
            container.style.display = 'none';
            document.body.style.overflow = 'auto';
            window.scrollTo(0, (window.originalScrollY || 0));
        }

        closeBtn.addEventListener('click', closePopup);
        overlay.addEventListener('click', closePopup);
        document.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ closePopup(); } });

        // expose small helpers for debugging
        window.setHiddenFavoriteIdAndTrigger = setHiddenFavoriteIdAndTrigger;
    })();
    </script>
    """)

demo.launch()
