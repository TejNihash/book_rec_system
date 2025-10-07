import ast
import pandas as pd
import gradio as gr
import random

# ---------------- Dataset ----------------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# ensure lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# add some defaults if missing
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# ---------------- Helpers ----------------
def create_book_card_html(book, favorites_ids):
    is_fav = book["id"] in (favorites_ids or [])
    rating = book.get("rating", 0)
    full = int(rating)
    stars = "⭐" * full + "☆" * (5 - full)
    if rating % 1 >= 0.5:
        stars = "⭐" * (full + 1) + "☆" * (4 - full)
    desc = book.get("description", "No description available.")
    fav_prefix = "❤️ " if is_fav else ""
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}"
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}"
         data-img="{book.get('image_url','')}" data-desc="{desc}"
         data-rating="{rating}" data-year="{book.get('year','N/A')}" data-pages="{book.get('pages','N/A')}">
        <div class='book-image-container'>
            <img src="{book.get('image_url','')}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year','N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{fav_prefix}{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages','N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df, favorites_ids=None, is_favorites_section=False):
    favorites_ids = favorites_ids or []
    if books_df is None or (hasattr(books_df, "empty") and books_df.empty):
        if is_favorites_section:
            return "<div style='text-align:center;padding:40px;color:#888;font-size:16px;'>No favorite books yet. Use the popup button to add some.</div>"
        return "<div style='text-align:center;padding:40px;color:#888;'>No books found</div>"
    if isinstance(books_df, list):
        books_df = pd.DataFrame(books_df)
    cards_html = [create_book_card_html(row, favorites_ids) for _, row in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------------- App ----------------
with gr.Blocks(css="""
/* dark theme + grid */
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:420px; overflow-y:auto; margin-bottom:20px; background:#111; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:14px; }
.book-card { background:#222; border-radius:10px; padding:10px; box-shadow:0 4px 14px rgba(0,0,0,0.6); cursor:pointer; transition:all 0.16s ease; border:1px solid #333; color:#eee; display:flex; flex-direction:column; height:100%; }
.book-card:hover { transform:translateY(-6px); box-shadow:0 14px 34px rgba(0,0,0,0.8); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:8px; }
.book-card img { width:100%; height:170px; object-fit:cover; border-radius:6px; border:1px solid #2b2b2b; }
.book-badge { position:absolute; top:8px; right:8px; background:#667eea; color:white; padding:2px 6px; border-radius:8px; font-size:11px; font-weight:700; }
.book-info { display:flex; flex-direction:column; gap:6px; flex:1; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.25; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.book-authors { font-size:11px; color:#9fb; }
.book-rating { font-size:12px; color:#f6b; }

/* popup */
.popup-overlay{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:99998; }
.popup-container{ display:none; position:fixed; background:#0f0f10; color:#eee; border-radius:12px; padding:14px; width:340px; max-height:78vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.8); border:1px solid #333; z-index:99999; transform-origin:top left; }
.popup-close{ position:absolute; top:8px; right:8px; background:#222; width:30px; height:30px; display:flex; align-items:center; justify-content:center; border-radius:50%; cursor:pointer; color:#fff; }
.popup-close:hover{ background:#667eea; }

/* favorite button style */
.favorite-btn{ background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%); color:white; border:none; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:700; }
.favorite-btn.saved{ background:linear-gradient(135deg,#48bb78 0%,#38a169 100%); }

/* misc */
.description-scroll { max-height:180px; overflow:auto; padding:8px; border-radius:8px; border:1px solid #222; margin-top:8px; background:#0d0d0d; color:#ddd; }
.favorites-count { background:#ed8936; color:white; padding:4px 10px; border-radius:12px; margin-left:12px; font-weight:700; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Click a book to open details; add to favorites from the popup.")

    # ---------- Hidden bridge components (JS -> Python) ----------
    # JS will set this textbox value and dispatch 'change' to trigger the Python handler
    favorite_book_id = gr.Textbox(visible=False, elem_id="current-book-id")
    # (No need for a separate hidden button - we use the change event on the textbox)

    # ---------- Favorites UI ----------
    favorites_state = gr.State([])  # list of book ids
    favorites_header = gr.HTML(
        """<div style="display:flex;align-items:center;margin-bottom:12px;">
               <h2 style="margin:0;color:#fff;border-left:4px solid #ed8936;padding-left:10px;">⭐ Favorites</h2>
               <div class="favorites-count">0 books</div>
           </div>"""
    )
    favorites_container = gr.HTML(elem_classes="books-section", value="<div style='text-align:center;padding:30px;color:#888;'>No favorite books yet.</div>")
    favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

    # ---------- Random & Popular sections ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
    shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    gr.Markdown("## 📈 Popular Books")
    popular_books_container = gr.HTML(elem_classes="books-section")
    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # ---------- States for paging ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)

    favorites_display_state = gr.State(pd.DataFrame())
    favorites_index_state = gr.State(0)

    # ---------- Python handler: triggered when hidden textbox changes -----------
    def on_fav_textbox_change(book_id, favorites_ids):
        # debug print to server logs
        print("PYTHON: on_fav_textbox_change called with:", book_id)
        favorites_ids = list(favorites_ids or [])
        if not book_id:
            return favorites_ids, gr.update(value=build_books_grid_html(pd.DataFrame(), favorites_ids)), gr.update(visible=False), gr.update(value="""
                <div style="display:flex;align-items:center;margin-bottom:12px;">
                    <h2 style="margin:0;color:#fff;border-left:4px solid #ed8936;padding-left:10px;">⭐ Favorites</h2>
                    <div class="favorites-count">0 books</div>
                </div>
            """)
        # toggle behavior: if exists remove, else add
        if book_id in favorites_ids:
            favorites_ids.remove(book_id)
            print("PYTHON: removed", book_id)
        else:
            favorites_ids.append(book_id)
            print("PYTHON: added", book_id)

        fav_df = df[df['id'].isin(favorites_ids)].reset_index(drop=True)
        fav_html = build_books_grid_html(fav_df, favorites_ids, is_favorites_section=True)
        load_more_vis = len(favorites_ids) > BOOKS_PER_LOAD
        header_html = f"""
            <div style="display:flex;align-items:center;margin-bottom:12px;">
                <h2 style="margin:0;color:#fff;border-left:4px solid #ed8936;padding-left:10px;">⭐ Favorites</h2>
                <div class="favorites-count">{len(favorites_ids)} book{'s' if len(favorites_ids)!=1 else ''}</div>
            </div>
        """
        return favorites_ids, gr.update(value=fav_html), gr.update(visible=load_more_vis), gr.update(value=header_html)

    favorite_book_id.change(
        fn=on_fav_textbox_change,
        inputs=[favorite_book_id, favorites_state],
        outputs=[favorites_state, favorites_container, favorites_load_more_btn, favorites_header]
    )

    # ---------- Loading / initial render ----------
    def initial_load(df_, favorites_ids):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books, favorites_ids)
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

    def shuffle_random_books(loaded, display):
        shuffled = loaded.sample(frac=1).reset_index(drop=True)
        initial = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial, favorites_state.value)
        return shuffled, initial, html, 1

    random_load_more_btn.click(load_more, [random_books_state, random_display_state, random_index_state],
                              [random_display_state, random_books_container, random_load_more_btn, random_index_state])
    shuffle_btn.click(shuffle_random_books, [random_books_state, random_display_state],
                      [random_books_state, random_display_state, random_books_container, random_index_state])
    popular_load_more_btn.click(load_more, [popular_books_state, popular_display_state, popular_index_state],
                                [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state])

    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value, favorites_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load(popular_books_state.value, favorites_state.value)
    favorites_state.value = []
    favorites_container.value = "<div style='text-align:center;padding:30px;color:#888;'>No favorite books yet.</div>"

    # ---------- Popup HTML + robust JS bridge ----------
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

        function escapeHtml(str){ return str ? String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;') : ''; }
        function formatText(text){ if(!text) return 'No description available.'; return text.replace(/\\n/g,'<br>'); }

        // robust helper: find the real input inside the Gradio wrapper (supports shadow DOM)
        function findInputInWrapper(wrapper){
            if(!wrapper) return null;
            let input = wrapper.querySelector('input, textarea');
            if(!input && wrapper.shadowRoot) input = wrapper.shadowRoot.querySelector('input, textarea');
            // sometimes Gradio nests another wrapper - search deeper
            if(!input){
                const deep = wrapper.querySelectorAll(':scope *');
                for(const el of deep){
                    if((el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')){ input = el; break; }
                    if(el.shadowRoot){
                        const inner = el.shadowRoot.querySelector('input, textarea');
                        if(inner){ input = inner; break; }
                    }
                }
            }
            return input;
        }

        // robust helper: find the real button inside a Gradio wrapper
        function findButtonInWrapper(wrapper){
            if(!wrapper) return null;
            let btn = wrapper.querySelector('button');
            if(!btn && wrapper.shadowRoot) btn = wrapper.shadowRoot.querySelector('button');
            if(!btn){
                const deep = wrapper.querySelectorAll(':scope *');
                for(const el of deep){
                    if(el.tagName === 'BUTTON'){ btn = el; break; }
                    if(el.shadowRoot){
                        const inner = el.shadowRoot.querySelector('button');
                        if(inner){ btn = inner; break; }
                    }
                }
            }
            return btn;
        }

        function setHiddenFavoriteIdAndTrigger(bookId){
            // wrapper created by gradio for elem_id="current-book-id"
            const wrapper = (typeof gradioApp === 'function') ? gradioApp().getElementById('current-book-id') : document.getElementById('current-book-id');
            if(!wrapper){ console.warn('fav wrapper not found'); return false; }
            const input = findInputInWrapper(wrapper);
            if(!input){ console.warn('fav input not found'); return false; }
            input.value = bookId;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            console.log('JS -> set hidden fav id:', bookId);
            return true;
        }

        // open popup next to clicked card
        function openPopupNearCard(card){
            const id = card.dataset.id;
            const title = escapeHtml(card.dataset.title);
            const authors = escapeHtml(card.dataset.authors);
            const genres = escapeHtml(card.dataset.genres);
            const desc = escapeHtml(card.dataset.desc);
            const img = escapeHtml(card.dataset.img || '');
            const rating = card.dataset.rating || '0';
            const year = card.dataset.year || 'N/A';
            const pages = card.dataset.pages || 'N/A';
            const numRating = parseFloat(rating);
            const full = Math.floor(numRating);
            const half = numRating % 1 >= 0.5;
            let stars = '⭐'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - (half?1:0));

            content.innerHTML = `
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <img src="${img}" style="width:120px;height:auto;border-radius:8px;object-fit:cover;">
                    <div style="flex:1;">
                        <h2 style="margin:0 0 6px 0;color:#fff;border-bottom:2px solid #667eea;padding-bottom:6px;">${title}</h2>
                        <p style="margin:6px 0;"><strong style="color:#88c">Author(s):</strong> <span style="color:#a0c4ff">${authors}</span></p>
                        <p style="margin:6px 0;"><strong style="color:#88c">Genres:</strong> <span style="color:#a78bfa">${genres}</span></p>
                        <p style="margin:6px 0;"><strong style="color:#88c">Rating:</strong> ${stars} <strong style="color:#ffa500">${parseFloat(rating).toFixed(1)}</strong></p>
                        <div class="detail-stats" style="margin-top:8px;">
                            <div class="detail-stat"><div class="detail-stat-value">${escapeHtml(year)}</div><div class="detail-stat-label">YEAR</div></div>
                            <div class="detail-stat"><div class="detail-stat-value">${escapeHtml(pages)}</div><div class="detail-stat-label">PAGES</div></div>
                            <div class="detail-stat"><div class="detail-stat-value">${Math.ceil(parseInt(pages)/250) || 'N/A'}</div><div class="detail-stat-label">READ HRS</div></div>
                        </div>
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <h3 style="margin:6px 0 8px 0;color:#fff;">Description</h3>
                    <div class="description-scroll">${formatText(desc)}</div>
                </div>
                <div style="margin-top:12px;">
                    <button class="favorite-btn" id="popup-fav-btn">❤️ Add to Favorites</button>
                </div>
            `;

            // position container near card (fixed)
            const rect = card.getBoundingClientRect();
            let top = rect.top;
            let left = rect.right + 10;
            container.style.transform = 'none';
            container.style.position = 'fixed';
            // show offscreen to compute dimensions
            container.style.top = '-9999px';
            container.style.left = '-9999px';
            container.style.display = 'block';
            overlay.style.display = 'block';
            // compute and adjust
            const cw = container.offsetWidth;
            const ch = container.offsetHeight;
            if(left + cw > window.innerWidth) left = rect.left - cw - 10;
            if(left < 8) left = 8;
            if(top + ch > window.innerHeight) top = Math.max(8, window.innerHeight - ch - 8);
            container.style.top = `${top}px`;
            container.style.left = `${left}px`;
            // lock background scroll
            document.body.style.overflow = 'hidden';

            // attach popup fav handler
            const popupFav = document.getElementById('popup-fav-btn');
            if(popupFav){
                popupFav.onclick = function(){
                    const ok = setHiddenFavoriteIdAndTrigger(id);
                    if(ok){
                        popupFav.classList.add('saved');
                        popupFav.textContent = '✅ Saved';
                        setTimeout(()=>{ popupFav.classList.remove('saved'); popupFav.textContent = '❤️ Add to Favorites'; }, 900);
                    } else {
                        console.warn('Could not trigger favorite change');
                    }
                };
            }
        }

        // event delegation for book-card clicks
        document.addEventListener('click', function(e){
            const card = e.target.closest('.book-card');
            if(!card) return;
            openPopupNearCard(card);
        });

        function closePopup(){
            overlay.style.display = 'none';
            container.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        closeBtn.addEventListener('click', closePopup);
        overlay.addEventListener('click', closePopup);
        document.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ closePopup(); } });

        // expose helper for debugging
        window.setHiddenFavoriteIdAndTrigger = setHiddenFavoriteIdAndTrigger;
    })();
    </script>
    """)

demo.launch()
