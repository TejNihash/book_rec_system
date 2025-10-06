import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12  # 2 rows of 6

# ---------- HTML rendering ----------
def make_books_html(start, count):
    subset = df.sample(frac=1).reset_index(drop=True).iloc[start:start+count]
    cards = []
    for _, book in subset.iterrows():
        card = f"""
        <div class='book-card' 
             data-id='{book['id']}'
             data-title="{book['title']}" 
             data-authors="{', '.join(book['authors'])}" 
             data-genres="{', '.join(book['genres'])}" 
             data-img="{book['image_url']}" 
             data-desc="{book.get('description', 'No description available.')}">
            <img src="{book['image_url']}" 
                 onerror="this.src='https://via.placeholder.com/120x180/667eea/ffffff?text=No+Image'"
                 class='book-cover'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>{', '.join(book['authors'])}</div>
        </div>
        """
        cards.append(card)
    return ''.join(cards)

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-wrapper {
    max-height: 600px;
    overflow-y: auto;
    background: #121212;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #333;
}

.books-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 15px;
    justify-items: center;
}

.book-card { 
    border:1px solid #444; 
    padding:10px; 
    border-radius:10px; 
    cursor:pointer; 
    transition: all 0.2s; 
    width:160px; 
    text-align:center;
    background:#1e1e1e; 
    color:#f5f5f5; 
    font-weight:bold; 
    flex:0 0 auto;
}
.book-card:hover { box-shadow:0 4px 16px rgba(255,255,255,0.15); transform:translateY(-2px);}
.book-cover { 
    width:100%; height:160px; object-fit:cover; border-radius:6px; margin-bottom:8px;
}
.book-title { font-size:13px; font-weight:bold; color:#fff; }
.book-authors { font-size:11px; color:#bbb; }

.books-wrapper::-webkit-scrollbar { width:8px; }
.books-wrapper::-webkit-scrollbar-thumb { background:#444; border-radius:4px; }

#detail-overlay {
    position:fixed; top:0; left:0; width:100%; height:100%;
    background:rgba(0,0,0,0.6); display:none; justify-content:center; align-items:center;
    z-index:999;
}
#detail-box {
    background:#f8f8f8; color:#111; padding:25px; border-radius:12px;
    width:750px; max-height:80vh; overflow-y:auto; box-shadow:0 4px 16px rgba(0,0,0,0.3);
    animation: fadeIn 0.2s ease-in-out;
}
#detail-close {
    position:absolute; top:15px; right:25px; font-size:22px; font-weight:bold; cursor:pointer;
}
@keyframes fadeIn {
    from { opacity:0; transform:scale(0.95); }
    to { opacity:1; transform:scale(1); }
}
""") as demo:

    gr.Markdown("# 📚 Book Explorer — Scrollable Library with Overlay Details")

    start_idx = gr.State(0)
    all_books_html = gr.HTML(value=f"<div class='books-container'>{make_books_html(0, BOOKS_PER_LOAD)}</div>")

    def load_more_books(current_html, start_idx):
        start_idx += BOOKS_PER_LOAD
        new_cards = make_books_html(start_idx, BOOKS_PER_LOAD)
        combined_html = current_html.replace("</div>", new_cards + "</div>")
        return combined_html, start_idx

    with gr.Column(elem_classes="books-wrapper"):
        all_books_html
        load_more_btn = gr.Button("📖 Load More Books")

    load_more_btn.click(load_more_books, inputs=[all_books_html, start_idx], outputs=[all_books_html, start_idx])

    # ---------- Overlay JS ----------
    gr.HTML("""<!-- Replace your existing overlay block with this -->
<div id="detail-overlay" style="display:none;">
  <div id="detail-box">
    <span id="detail-close">&times;</span>
    <div id="detail-content"></div>
  </div>
</div>

<script>
(function(){
  const overlay = document.getElementById('detail-overlay');
  const box = document.getElementById('detail-box');
  const closeBtn = document.getElementById('detail-close');

  // Keep track of which card opened the overlay so we can reposition on scroll/resize
  let currentCard = null;

  // Show overlay and position near the card (fixed positioning)
  function showOverlayAt(card, html) {
    currentCard = card;
    document.getElementById('detail-content').innerHTML = html;

    // Make overlay visible (but hide content until we place it)
    overlay.style.display = 'block';
    box.style.position = 'fixed';
    box.style.visibility = 'hidden';
    box.style.left = '0px';
    box.style.top = '0px';

    // Allow browser to render and measure
    requestAnimationFrame(() => {
      positionBoxNearCard(card);
      box.style.visibility = 'visible';
    });
  }

  // Position the box near the card, but clamp to viewport bounds
  function positionBoxNearCard(card) {
    if (!card || overlay.style.display === 'none') return;

    const rect = card.getBoundingClientRect();
    const boxRect = box.getBoundingClientRect();
    const margin = 12;

    // Prefer vertically centering the box on the card.
    let top = rect.top + rect.height / 2 - boxRect.height / 2;
    let left = rect.left + rect.width / 2 - boxRect.width / 2;

    // If card is near the left edge or right edge, try to align box to the right/left of card
    // (optional heuristic — you can tweak)
    if (left < margin) {
      left = rect.right + 8; // place to right of card
    } else if (left + boxRect.width > window.innerWidth - margin) {
      left = rect.left - boxRect.width - 8; // place to left of card
    }

    // Clamp into viewport
    top = Math.max(margin, Math.min(top, window.innerHeight - boxRect.height - margin));
    left = Math.max(margin, Math.min(left, window.innerWidth - boxRect.width - margin));

    // If box is too tall for viewport, center it vertically
    if (boxRect.height + 2 * margin > window.innerHeight) {
      top = margin;
    }

    box.style.left = Math.round(left) + 'px';
    box.style.top = Math.round(top) + 'px';
  }

  // Build detail HTML from card data (you can expand this)
  function buildDetailHTML(card) {
    const title = card.dataset.title || '';
    const authors = card.dataset.authors || '';
    const genres = card.dataset.genres || '';
    const desc = card.dataset.desc || '';
    const img = card.dataset.img || '';

    return `
      <div style="display:flex;gap:20px;align-items:flex-start;">
        <img src="${img}" style="width:220px;height:auto;border-radius:8px;object-fit:cover;">
        <div style="max-width:470px;">
          <h2 style="margin:0 0 10px 0;">${escapeHtml(title)}</h2>
          <p style="margin:6px 0;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
          <p style="margin:6px 0;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
          <div style="margin-top:10px;line-height:1.6;color:#333;">${escapeHtml(desc)}</div>
        </div>
      </div>
    `;
  }

  // Simple HTML escaper to avoid accidental HTML injection from content
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Click handler: open overlay near clicked card
  document.addEventListener('click', function(e) {
    const card = e.target.closest('.book-card');
    if (!card) return;

    const html = buildDetailHTML(card);
    showOverlayAt(card, html);
  });

  // Close handlers
  closeBtn.addEventListener('click', () => {
    overlay.style.display = 'none';
    currentCard = null;
  });

  overlay.addEventListener('click', (e) => {
    // close when clicking the dim area (but not when clicking inside the box)
    if (e.target === overlay) {
      overlay.style.display = 'none';
      currentCard = null;
    }
  });

  // ESC key closes overlay
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      overlay.style.display = 'none';
      currentCard = null;
    }
  });

  // Reposition overlay while open when user scrolls or resizes
  window.addEventListener('scroll', () => {
    if (overlay.style.display === 'block' && currentCard) {
      requestAnimationFrame(() => positionBoxNearCard(currentCard));
    }
  }, true); // capture scrolls in ancestors too

  window.addEventListener('resize', () => {
    if (overlay.style.display === 'block' && currentCard) {
      requestAnimationFrame(() => positionBoxNearCard(currentCard));
    }
  });
})();
</script>
    """)

demo.launch()
