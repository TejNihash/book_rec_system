import pandas as pd
import ast
import random
import gradio as gr

# ---------------- Data loading ----------------
df = pd.read_csv("data_mini_books.csv")

# Ensure id exists
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Convert stringified lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Fill missing fields if any
df["rating"] = df.get("rating", [round(random.uniform(3.5, 4.8), 1) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# Start with a shuffled subset to display
shuffled_df = df.sample(frac=1, random_state=42).reset_index(drop=True)
displayed_ids_init = list(shuffled_df.iloc[:BOOKS_PER_LOAD]["id"])

# Global favorites storage (simple server-side list)
favorites_list = []

# ---------------- Helper HTML builders ----------------
def build_books_grid_html_from_ids(id_list):
    """Build grid HTML for the given list of book ids (keeps order)."""
    if not id_list:
        return "<div style='color:#888; padding:12px;'>No books to show.</div>"
    rows = []
    for book_id in id_list:
        book = df[df["id"] == book_id]
        if book.empty:
            continue
        b = book.iloc[0].to_dict()
        is_fav = any(f["id"] == b["id"] for f in favorites_list)
        heart = "❤️" if is_fav else "🤍"
        # Card HTML: data-id, clickable card and heart with handlers
        card = f"""
        <div class="book-card" data-id="{b['id']}" onclick="onCardClick(event, '{b['id']}', this)">
            <div class="heart" onclick="onHeartClick(event, '{b['id']}')">{heart}</div>
            <img src="{b.get('image_url','')}" onerror="this.src='https://via.placeholder.com/140x200/444/fff?text=No+Image'"/>
            <div class='card-title'>{escape_html(b.get('title','Untitled'))}</div>
            <div class='card-authors'>{escape_html(', '.join(b.get('authors',[])))}</div>
        </div>
        """
        rows.append(card)
    return "<div class='books-grid'>" + "".join(rows) + "</div>"

def build_favorites_html():
    if not favorites_list:
        return "<div style='color:#888; padding:12px;'>No favorites yet.</div>"
    cards = []
    for b in favorites_list:
        cards.append(f"""
        <div class="fav-card">
            <img src="{b.get('image_url','')}" onerror="this.src='https://via.placeholder.com/100x140/444/fff?text=No+Image'"/>
            <div class="fav-title">{escape_html(b.get('title','Untitled'))}</div>
        </div>
        """)
    return "<div class='favorites-grid'>" + "".join(cards) + "</div>"

def get_details_html(book_id):
    book = df[df["id"] == book_id]
    if book.empty:
        return "<div style='color:#aaa; padding:12px;'>Book not found.</div>"
    b = book.iloc[0].to_dict()
    rating = b.get("rating", 0)
    full_stars = "⭐" * int(rating)
    if rating % 1 >= 0.5:
        full_stars += "½"
    full_stars += "☆" * max(0, 5 - len(full_stars))
    desc = escape_html(b.get("description", "No description available."))
    authors = escape_html(", ".join(b.get("authors", [])))
    genres = escape_html(", ".join(b.get("genres", [])))
    html = f"""
    <div class="details-inner">
        <img src="{b.get('image_url','')}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'"/>
        <div class="details-info">
            <h3>{escape_html(b.get('title','Untitled'))}</h3>
            <p><strong>Authors:</strong> {authors}</p>
            <p><strong>Genres:</strong> {genres}</p>
            <p><strong>Year:</strong> {b.get('year','N/A')} &nbsp; | &nbsp; <strong>Pages:</strong> {b.get('pages','N/A')}</p>
            <p><strong>Rating:</strong> {full_stars} ({rating:.1f})</p>
            <div class="desc">{desc}</div>
            <div style="margin-top:10px;">
                <button onclick="onHeartClick(event, '{b['id']}')" class="inline-heart">Toggle ❤️</button>
            </div>
        </div>
    </div>
    """
    return html

# small helper to safely escape text used inside HTML
def escape_html(s: str):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )

# ---------------- Server-side handlers ----------------
def handle_show_details(book_id_str):
    """Returns details HTML for the panel (single output)."""
    return get_details_html(book_id_str)

def handle_toggle_favorite(book_id_str, displayed_ids):
    """Toggle favorite and return (grid_html, favorites_html, details_html_or_empty)"""
    global favorites_list
    # toggle
    target = df[df["id"] == book_id_str]
    if target.empty:
        # nothing changed
        grid_html = build_books_grid_html_from_ids(displayed_ids)
        fav_html = build_favorites_html()
        details_html = "<div style='color:#aaa; padding:12px;'>Book not found.</div>"
        return grid_html, fav_html, details_html

    book = target.iloc[0].to_dict()
    if any(f["id"] == book_id_str for f in favorites_list):
        favorites_list = [f for f in favorites_list if f["id"] != book_id_str]
    else:
        favorites_list.append(book)

    grid_html = build_books_grid_html_from_ids(displayed_ids)
    fav_html = build_favorites_html()
    # update details panel to reflect new heart state if open
    details_html = get_details_html(book_id_str)
    return grid_html, fav_html, details_html

# ---------------- UI / Layout ----------------
initial_grid_html = build_books_grid_html_from_ids(displayed_ids_init)
initial_fav_html = build_favorites_html()
initial_details_html = "<div style='color:#888; padding:12px;'>Click a card to see details here.</div>"

css = r"""
/* Grid & cards */
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}
.book-card {
  position: relative;
  background: #222;
  padding: 8px;
  border-radius: 10px;
  color: #eee;
  cursor: pointer;
  transition: transform 0.12s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.book-card:hover { transform: translateY(-6px); }
.book-card img { width: 100%; height: 180px; object-fit: cover; border-radius: 6px; }
.card-title { font-weight:700; margin-top:6px; font-size:13px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
.card-authors { font-size:12px; color:#9fb; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; margin-top:4px; }

/* heart in corner */
.book-card .heart {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
  cursor: pointer;
  user-select: none;
}

/* floating details panel */
#details_panel {
  position: absolute;
  z-index: 9999;
  display: none;
  min-width: 320px;
  max-width: 420px;
  background: #111;
  border: 1px solid #333;
  padding: 12px;
  border-radius: 10px;
  color: #eee;
  box-shadow: 0 12px 36px rgba(0,0,0,0.6);
}

/* details inner */
.details-inner { display:flex; gap:12px; }
.details-inner img { width:140px; height:210px; object-fit:cover; border-radius:6px; }
.details-info h3 { margin:0 0 8px 0; color:#fff; }
.details-info .desc { margin-top:8px; color:#ccc; max-height:120px; overflow:auto; }

/* small favorites */
.favorites-grid { display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
.fav-card { background:#222; padding:6px; border-radius:8px; width:100px; text-align:center; color:#eee; }
.fav-card img { width:80px; height:110px; object-fit:cover; border-radius:5px; }

/* inline heart button in details */
.inline-heart { background:linear-gradient(135deg,#ed8936,#dd6b20); color:white; border:none; padding:8px 12px; border-radius:10px; cursor:pointer; }
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("Click a card to open a details panel beside it. Click the ❤️ to add/remove favorites (updates Favorites below).")

    # Top area with the grid
    with gr.Row():
        with gr.Column(scale=3):
            # The grid of cards (HTML)
            random_grid = gr.HTML(value=initial_grid_html, elem_id="random_grid")
        # details panel element (we will update it and position it via JS)
        details_panel = gr.HTML(value=initial_details_html, elem_id="details_panel")
    # Favorites area
    gr.Markdown("## ⭐ Favorites")
    favorites_box = gr.HTML(value=initial_fav_html, elem_id="favorites_box")

    # Hidden Gradio inputs/buttons used as "bridges" from JS -> Python
    hidden_details_input = gr.Textbox(value="", visible=False, elem_id="hidden_details_input")
    hidden_details_btn = gr.Button("hidden_details_btn", visible=False, elem_id="hidden_details_btn")
    hidden_toggle_input = gr.Textbox(value="", visible=False, elem_id="hidden_toggle_input")
    hidden_toggle_btn = gr.Button("hidden_toggle_btn", visible=False, elem_id="hidden_toggle_btn")

    # State storing currently displayed ids so we re-render the same grid after toggles
    displayed_ids_state = gr.State(displayed_ids_init)

    # Bind hidden buttons to server functions
    hidden_details_btn.click(
        fn=handle_show_details,
        inputs=[hidden_details_input],
        outputs=[details_panel]
    )

    hidden_toggle_btn.click(
        fn=handle_toggle_favorite,
        inputs=[hidden_toggle_input, displayed_ids_state],
        outputs=[random_grid, favorites_box, details_panel]
    )

    # Insert JS after elements so it can find them.
    gr.HTML(
    """
    <script>
    // Called when clicking a card (the HTML uses onclick="onCardClick(...)")
    function onCardClick(e, bookId, el) {
        e.stopPropagation();
        // position details panel near the clicked element
        const detailsPanel = document.getElementById('details_panel');
        if (!detailsPanel) return;
        // compute position to the right if space, else to left
        const rect = el.getBoundingClientRect();
        const panelWidth = 420;
        const pageWidth = window.innerWidth;
        const gap = 8;
        let left = rect.right + window.scrollX + gap;
        if (left + panelWidth > pageWidth - 10) {
            left = rect.left + window.scrollX - panelWidth - gap;
            if (left < 10) left = 10;
        }
        let top = rect.top + window.scrollY;
        if (top + 300 > window.innerHeight + window.scrollY) {
            top = Math.max(10, window.innerHeight + window.scrollY - 320);
        }

        detailsPanel.style.left = left + "px";
        detailsPanel.style.top = top + "px";
        detailsPanel.style.display = "block";

        // set hidden input and click hidden details button (to call Python)
        const container = document.getElementById('hidden_details_input');
        const input = container ? container.querySelector('input') : null;
        const btnRoot = document.getElementById('hidden_details_btn');
        const btn = btnRoot ? btnRoot.querySelector('button') : null;
        if (input && btn) {
            input.value = bookId;
            // click the inner button element
            btn.click();
        } else {
            console.error('Hidden details components not found in DOM.');
        }
    }

    // Called when clicking the heart (toggle)
    function onHeartClick(e, bookId) {
        e.stopPropagation(); // avoid also triggering the card click
        const container = document.getElementById('hidden_toggle_input');
        const input = container ? container.querySelector('input') : null;
        const btnRoot = document.getElementById('hidden_toggle_btn');
        const btn = btnRoot ? btnRoot.querySelector('button') : null;
        if (input && btn) {
            input.value = bookId;
            btn.click();
        } else {
            console.error('Hidden toggle components not found in DOM.');
        }
    }

    // Hide details when clicking outside
    document.addEventListener('click', function(ev) {
        const panel = document.getElementById('details_panel');
        if (!panel) return;
        const insidePanel = panel.contains(ev.target);
        const card = ev.target.closest('.book-card');
        if (!insidePanel && !card) {
            panel.style.display = 'none';
        }
    });

    // Optional: reposition details panel on window resize (hide)
    window.addEventListener('resize', () => {
        const panel = document.getElementById('details_panel');
        if (panel) panel.style.display = 'none';
    });
    </script>
    """
    )

# That's it — launch the app
demo.launch()
