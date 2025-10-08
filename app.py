import ast
import pandas as pd
import gradio as gr
import random

# ---------------- Data loading ----------------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# convert authors/genres if stored as strings
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# ensure some fields
df["rating"] = df.get("rating", [round(random.uniform(3.5, 4.8), 1) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# ---------------- Helpers ----------------
def escape_html(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")

def create_book_card_html(book, is_fav=False):
    """Create card HTML with Add/Remove favorites button text (not icon)."""
    fav_text = "Remove from Favorites" if is_fav else "Add to Favorites"
    return f"""
    <div class='book-card' data-id="{escape_html(book['id'])}"
         data-title="{escape_html(book['title'])}"
         data-authors="{escape_html(', '.join(book['authors']))}"
         data-genres="{escape_html(', '.join(book['genres']))}"
         data-img="{escape_html(book.get('image_url',''))}"
         data-desc="{escape_html(book.get('description','No description available.'))}">
        <img src="{escape_html(book.get('image_url',''))}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class='book-title'>{escape_html(book['title'])}</div>
        <div class='book-authors'>by {escape_html(', '.join(book['authors']))}</div>
        <button class='fav-btn' data-id="{escape_html(book['id'])}" title="{escape_html(fav_text)}">{escape_html(fav_text)}</button>
    </div>
    """

def build_books_grid_html(books_df, favorites_ids):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards = []
    for _, b in books_df.iterrows():
        cards.append(create_book_card_html(b, is_fav=(b["id"] in favorites_ids)))
    return f"<div class='books-grid'>{''.join(cards)}</div>"

def build_favorites_sidebar_html(favorites_ids):
    if not favorites_ids:
        return "<div class='sidebar-empty'>No favorites yet.</div>"
    favs = df[df["id"].isin(favorites_ids)]
    items = []
    for _, r in favs.iterrows():
        items.append(f"""
        <div class="sidebar-book" data-id="{escape_html(r['id'])}">
            <img src="{escape_html(r.get('image_url',''))}" onerror="this.src='https://via.placeholder.com/36x52/ddd/888?text=No'"/>
            <div>
                <div class="sidebar-book-title">{escape_html(r['title'])}</div>
                <div style="font-size:12px;color:#666;">by {escape_html(', '.join(r['authors'][:2]))}</div>
            </div>
        </div>
        """)
    return "<div class='favorites-list'>" + "".join(items) + "</div>"

def get_details_html(book_id, favorites_ids):
    row = df[df["id"] == book_id]
    if row.empty:
        return "<div style='padding:12px;color:#666;'>Book not found.</div>"
    b = row.iloc[0]
    is_fav = book_id in favorites_ids
    fav_button_text = "Remove from Favorites" if is_fav else "Add to Favorites"
    rating = b.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        # treat half-star visually as a half character (approx)
        stars = "⭐" * (int(rating)) + "½" + "☆" * max(0, 4 - int(rating))
    return f"""
    <div class="details-inner">
        <img src="{escape_html(b.get('image_url',''))}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'"/>
        <div class="details-info">
            <h3>{escape_html(b['title'])}</h3>
            <p><strong>Authors:</strong> {escape_html(', '.join(b['authors']))}</p>
            <p><strong>Genres:</strong> {escape_html(', '.join(b['genres']))}</p>
            <p><strong>Year:</strong> {escape_html(b.get('year','N/A'))} &nbsp; | &nbsp; <strong>Pages:</strong> {escape_html(b.get('pages','N/A'))}</p>
            <p><strong>Rating:</strong> {stars} ({rating:.1f})</p>
            <div class="desc">{escape_html(b.get('description','No description'))}</div>
            <div style="margin-top:12px;">
                <button class="details-fav-btn" data-id="{escape_html(b['id'])}">{escape_html(fav_button_text)}</button>
            </div>
        </div>
    </div>
    """

# ---------------- Server-side handlers ----------------
def load_more(loaded_books, display_books, page_idx, favorites_ids):
    """Generic load_more used by random and popular sections."""
    start = page_idx * BOOKS_PER_LOAD
    end = start + BOOKS_PER_LOAD
    new_books = loaded_books.iloc[start:end]
    if new_books.empty:
        # no more
        html = build_books_grid_html(display_books, favorites_ids)
        return display_books, gr.update(value=html), page_idx
    combined = pd.concat([display_books, new_books], ignore_index=True)
    html = build_books_grid_html(combined, favorites_ids)
    return combined, gr.update(value=html), page_idx + 1

def toggle_favorite_server(book_id, favorites_ids, displayed_ids):
    """Toggle favorite on server and return updated HTML for grid, sidebar, details."""
    if favorites_ids is None:
        favorites_ids = []
    # make a copy (state will be updated by Gradio)
    favs = list(favorites_ids)
    if book_id in favs:
        favs.remove(book_id)
    else:
        favs.append(book_id)
    # update grid (re-render same displayed ids to preserve paging)
    displayed_df = df[df["id"].isin(displayed_ids)].copy()
    grid_html = build_books_grid_html(displayed_df, favs)
    sidebar_html = build_favorites_sidebar_html(favs)
    # return updated details panel for the same book (so button text updates)
    details_html = get_details_html(book_id, favs)
    return favs, gr.update(value=grid_html), gr.update(value=sidebar_html), gr.update(value=details_html)

def show_details_server(book_id, favorites_ids):
    html = get_details_html(book_id, favorites_ids)
    return gr.update(value=html)

# ---------------- UI ----------------
css = r"""
/* Layout */
.app-wrap { display:flex; gap:12px; padding:12px; box-sizing:border-box; }
.main-content { flex:1; overflow-y:auto; padding-right:12px; max-width:calc(100% - 320px); }
.sidebar { width:320px; position:fixed; right:12px; top:12px; bottom:12px; background:#f7f7f7; border-left:1px solid #ddd; padding:12px; overflow:auto; border-radius:8px; }
.sidebar h3 { margin-top:0; }

/* Books grid */
.books-section { border:1px solid #e0e0e0; border-radius:12px; padding:12px; margin-bottom:16px; background:#fff; }
.books-grid { display:grid; grid-template-columns: repeat(6,1fr); gap:12px; }
.book-card { background:#fff; border-radius:8px; padding:6px; box-shadow:0 2px 6px rgba(0,0,0,0.06); cursor:pointer; text-align:center; position:relative; }
.book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
.book-title { font-size:12px; font-weight:700; color:#222; height:36px; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;}
.book-authors { font-size:11px; color:#666; margin-bottom:6px; }

/* fav button on card */
.fav-btn { display:inline-block; border:1px solid #667eea; background:#667eea; color:#fff; padding:6px 8px; border-radius:6px; font-size:12px; cursor:pointer; }
.fav-btn.remove { background:#ddd; color:#333; border-color:#bbb; }

/* details panel */
#detail-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:1000; }
#detail-box { position:absolute; background:#fff; border-radius:8px; padding:16px; max-width:560px; box-shadow:0 8px 20px rgba(0,0,0,0.35); color:#111; }
.details-inner { display:flex; gap:12px; }
.details-inner img { width:150px; height:220px; object-fit:cover; border-radius:6px; }
.details-info h3 { margin:0 0 6px 0; }
.details-info .desc { margin-top:8px; color:#444; max-height:140px; overflow:auto; }

/* favorites sidebar items */
.sidebar .favorites-list { display:flex; flex-direction:column; gap:8px; }
.sidebar-book { display:flex; gap:8px; align-items:center; background:#fff; padding:8px; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.04); }
.sidebar-book img { width:44px; height:66px; object-fit:cover; border-radius:4px; }
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown("# 🎲 Random & Popular Books (upgraded)")

    # states
    favorites_state = gr.State([])  # list of ids
    # create shuffled random and popular states
    random_loaded_state = gr.State(df.sample(frac=1, random_state=42).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_page_state = gr.State(0)

    popular_loaded_state = gr.State(df.copy().reset_index(drop=True))
    popular_display_state = gr.State(pd.DataFrame())
    popular_page_state = gr.State(0)

    # UI layout: left main + right sidebar
    gr.HTML('<div class="app-wrap">')
    with gr.Column(elem_classes="main-content"):
        # Random section
        gr.Markdown("## 🎲 Random Books")
        random_container = gr.HTML()
        random_load_btn = gr.Button("📚 Load More Random Books")

        # Popular section
        gr.Markdown("## 📈 Popular Books")
        popular_container = gr.HTML()
        popular_load_btn = gr.Button("📚 Load More Popular Books")

        # Details overlay (hidden initially)
        details_overlay = gr.HTML("""<div id="detail-overlay"><div id="detail-box"><div id="detail-content">Click a book to see details.</div></div></div>""", elem_id="detail_html")
    with gr.Column(elem_classes="sidebar"):
        gr.Markdown("## ⭐ Favorites")
        favorites_container = gr.HTML("<div class='sidebar-inner'><div>No favorites yet.</div></div>")

    gr.HTML('</div>')  # close app-wrap

    # Hidden Gradio components that JS will use to call Python handlers
    # We rely on their elem_id to locate internal input/button elements in DOM.
    fav_toggle_input = gr.Textbox(visible=False, elem_id="fav_toggle_input")
    fav_toggle_btn = gr.Button(visible=False, elem_id="fav_toggle_btn")
    details_input = gr.Textbox(visible=False, elem_id="details_input")
    details_btn = gr.Button(visible=False, elem_id="details_btn")

    # ---------- Bind python functions to hidden buttons ----------
    # Random load_more
    def load_more_random(loaded, display, page_idx, favs):
        return load_more(loaded, display, page_idx, favs)
    random_load_btn.click(
        load_more_random,
        [random_loaded_state, random_display_state, random_page_state, favorites_state],
        [random_display_state, random_container, random_page_state],
    )
    # Popular load_more
    def load_more_popular(loaded, display, page_idx, favs):
        return load_more(loaded, display, page_idx, favs)
    popular_load_btn.click(
        load_more_popular,
        [popular_loaded_state, popular_display_state, popular_page_state, favorites_state],
        [popular_display_state, popular_container, popular_page_state],
    )

    # Hidden toggle favorite button wired to server
    fav_toggle_btn.click(
        toggle_favorite_server,
        [fav_toggle_input, favorites_state, gr.State(list(df.iloc[:BOOKS_PER_LOAD]["id"]))],  # pass displayed ids (initially first page)
        [favorites_state, random_container, favorites_container, details_overlay],
    )

    # Hidden details button wired to server
    details_btn.click(
        show_details_server,
        [details_input, favorites_state],
        [details_overlay],
    )

    # Initial populate for random & popular
    def initial_load(loaded_books, favs):
        disp, html_update, nxt = load_more(loaded_books, pd.DataFrame(), 0, favs)
        # return state, html value, next_page_index
        return disp, html_update, nxt

    random_display_state.value, random_container.value, random_page_state.value = initial_load(random_loaded_state.value, [])
    popular_display_state.value, popular_container.value, popular_page_state.value = initial_load(popular_loaded_state.value, [])

    # ---------- Client-side JS (robust) ----------
    # This script uses event delegation for .fav-btn and .book-card clicks.
    # It finds the hidden Gradio components by elem_id (wrapper) and then searches for the inner input/button.
    gr.HTML(r"""
<script>
/* Utils to find inner input/button within Gradio-provided wrapper by elem_id */
function findInputInWrapper(elemId) {
    const wrapper = document.getElementById(elemId);
    if (!wrapper) return null;
    // try common locations
    const input = wrapper.querySelector('input[type="text"], input[type="hidden"], textarea');
    if (input) return input;
    // older Gradio may use input inside a shadow or nested element
    const possible = wrapper.querySelectorAll('input, textarea');
    return possible.length ? possible[0] : null;
}
function findButtonInWrapper(elemId) {
    const wrapper = document.getElementById(elemId);
    if (!wrapper) return null;
    const btn = wrapper.querySelector('button');
    if (btn) return btn;
    // fallback: look for role=button element
    const roleBtn = wrapper.querySelector('[role="button"]');
    return roleBtn || null;
}

/* Favorites map used purely on client for display (server is source of truth).
   BUT we will update server via hidden Gradio button and rely on server to return updated HTML. */
document.addEventListener('click', function(e) {
    // If a favorites button on card was clicked
    const favBtn = e.target.closest('.fav-btn');
    if (favBtn) {
        e.stopPropagation();
        const bookId = favBtn.dataset.id;
        // Defensive find of hidden input/button elements
        const input = findInputInWrapper('fav_toggle_input');
        const btn = findButtonInWrapper('fav_toggle_btn');
        if (input && btn) {
            input.value = bookId;
            // click inner button element to trigger Gradio
            btn.click();
        } else {
            console.error('[DEBUG] fav hidden components not found', {input, btn});
            alert('Internal error: cannot call favorite handler. Check console.');
        }
        return;
    }

    // If details panel button inside details clicked (toggle inside details)
    const detailsFavBtn = e.target.closest('.details-fav-btn');
    if (detailsFavBtn) {
        e.stopPropagation();
        const bookId = detailsFavBtn.dataset.id;
        const input = findInputInWrapper('fav_toggle_input');
        const btn = findButtonInWrapper('fav_toggle_btn');
        if (input && btn) {
            input.value = bookId;
            btn.click();
        } else {
            console.error('[DEBUG] fav hidden components not found (details)');
        }
        return;
    }

    // If clicking a book card (open details)
    const card = e.target.closest('.book-card');
    if (card) {
        const bookId = card.dataset.id;
        // Position overlay details box next to the card
        const overlay = document.getElementById('detail-overlay');
        const box = document.getElementById('detail-box');
        const rect = card.getBoundingClientRect();
        // compute left/top for the detail box (prefer right side)
        const boxWidth = 560;
        let left = rect.right + 8 + window.scrollX;
        if (left + boxWidth > window.innerWidth - 10) {
            left = Math.max(10, rect.left - boxWidth - 8 + window.scrollX);
        }
        let top = rect.top + window.scrollY;
        overlay.style.display = 'block';
        box.style.left = left + 'px';
        box.style.top = top + 'px';
        // call hidden details button to ask server for details HTML
        const input = findInputInWrapper('details_input');
        const btn = findButtonInWrapper('details_btn');
        if (input && btn) {
            input.value = bookId;
            btn.click();
        } else {
            console.error('[DEBUG] details hidden components not found', {input, btn});
            // fallback: show client-side quick details
            const content = document.getElementById('detail-content');
            content.innerHTML = '<div style="padding:12px;color:#666;">Could not fetch details (internal error).</div>';
        }
        return;
    }
}, true);

/* Close overlay handlers */
document.addEventListener('click', function(e) {
    const overlay = document.getElementById('detail-overlay');
    if (!overlay) return;
    const closeBtn = document.getElementById('detail-box');
    // if clicked outside the box, hide
    if (overlay.style.display === 'block' && !e.target.closest('#detail-box')) {
        overlay.style.display = 'none';
    }
});

/* Ensure the overlay close button hides it */
window.addEventListener('load', () => {
    // Add a close icon inside the detail box if not present
    const detailBox = document.getElementById('detail-box');
    if (detailBox && !document.getElementById('detail-close')) {
        const span = document.createElement('span');
        span.id = 'detail-close';
        span.innerHTML = '&times;';
        span.style.position = 'absolute';
        span.style.top = '8px';
        span.style.right = '12px';
        span.style.cursor = 'pointer';
        span.style.fontSize = '20px';
        detailBox.appendChild(span);
        span.addEventListener('click', () => {
            const overlay = document.getElementById('detail-overlay');
            overlay.style.display = 'none';
        });
    }
});
</script>
    """)

# Launch
demo.launch()
