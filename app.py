import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12  # 2 columns * 6 rows

# ---------- Helpers ----------
def book_card_text(book, expanded=False):
    if expanded:
        return f"{book['title']}\nby {', '.join(book['authors'])}\nGenres: {', '.join(book['genres'])}\n\n{book.get('description','No description')}"
    else:
        return f"{book['title']}\nby {', '.join(book['authors'])}"

def get_books_page(books_df, page):
    start = page * BOOKS_PER_LOAD
    end = start + BOOKS_PER_LOAD
    return books_df.iloc[start:end]

# ---------- Callbacks ----------
def load_more(section, page, displayed_ids):
    books_df = df.sample(frac=1).reset_index(drop=True) if section=="random" else df.copy()
    next_books = get_books_page(books_df, page)
    new_display = []
    for _, book in next_books.iterrows():
        if book["id"] not in displayed_ids:
            new_display.append((book_card_text(book), book["id"]))
            displayed_ids.append(book["id"])
    return new_display, page+1, displayed_ids

def expand_card(book_id):
    book = df[df["id"]==book_id].iloc[0]
    return book_card_text(book, expanded=True)

def collapse_all_cards(displayed_ids):
    cards = []
    for bid in displayed_ids:
        book = df[df["id"]==bid].iloc[0]
        cards.append((book_card_text(book, expanded=False), bid))
    return cards

# ---------- Gradio UI ----------
with gr.Blocks() as demo:
    gr.Markdown("# 📚 Book Explorer (Button Version)")

    with gr.Column():
        gr.Markdown("🎲 Random Books")
        random_display = gr.Column()
        load_random_btn = gr.Button("📚 Load More Random")
        collapse_random_btn = gr.Button("Collapse All")
        random_page = gr.State(0)
        random_displayed_ids = gr.State([])

    with gr.Column():
        gr.Markdown("📚 Popular Books")
        popular_display = gr.Column()
        load_popular_btn = gr.Button("📚 Load More Popular")
        collapse_popular_btn = gr.Button("Collapse All")
        popular_page = gr.State(0)
        popular_displayed_ids = gr.State([])

    # ---------- Load More ----------
    load_random_btn.click(load_more, 
                          inputs=["random", random_page, random_displayed_ids],
                          outputs=[random_display, random_page, random_displayed_ids])

    load_popular_btn.click(load_more, 
                           inputs=["popular", popular_page, popular_displayed_ids],
                           outputs=[popular_display, popular_page, popular_displayed_ids])

    # ---------- Collapse ----------
    collapse_random_btn.click(collapse_all_cards,
                              inputs=[random_displayed_ids],
                              outputs=random_display)
    
    collapse_popular_btn.click(collapse_all_cards,
                              inputs=[popular_displayed_ids],
                              outputs=popular_display)

    # ---------- Expand card ----------
    # Each button in display column automatically expands via its callback
    # (gr.Button inside Column can be generated dynamically from returned list)

demo.launch()
