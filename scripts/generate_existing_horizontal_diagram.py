"""
Script to generate the Existing Legal AI Pipeline diagram in horizontal layout.
Direct visual counterpart to the proposed CiteJustice pipeline diagram.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

import os

def create_existing_horizontal_pipeline(output_path=None):
    if output_path is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(root_dir, "Images", "Pipelines", "Existing_Pipeline_Horizontal.png")
    # Wide horizontal layout matching the user's diagram proportions
    fig, ax = plt.subplots(figsize=(19, 4.2), facecolor='#202020')
    ax.set_facecolor('#202020')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Draw outer container card with subtle border
    outer_card = patches.FancyBboxPatch(
        (1.5, 4), 97, 92,
        boxstyle="round,pad=1.0,rounding_size=1.5",
        facecolor="#181818",
        edgecolor="#383838",
        linewidth=1.5
    )
    ax.add_patch(outer_card)

    # Title at top center
    ax.text(
        50, 91.5,
        "Existing Legal AI Pipeline\nSimilarity-Based RAG (Precedent-Blind)",
        color="#e2e8f0",
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        linespacing=1.25,
        family="sans-serif"
    )

    # Function to draw styled dark node box
    def draw_box(x, y, w, h, text, edge_color="#555555", face_color="#121212", text_color="#ffffff", bold=False, font_size=10.5):
        box = patches.FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="square,pad=0.4",
            facecolor=face_color,
            edgecolor=edge_color,
            linewidth=1.2,
            zorder=3
        )
        ax.add_patch(box)
        ax.text(
            x, y, text,
            color=text_color,
            fontsize=font_size,
            fontweight="bold" if bold else "normal",
            ha="center",
            va="center",
            linespacing=1.3,
            family="sans-serif",
            zorder=4
        )
        return box

    # Node positions along horizontal X-axis (Y centered at 44)
    y_center = 44.0

    # 1. New Case Facts (x=10.0)
    draw_box(10.0, y_center, 13.0, 34, "New Case Facts: IPC 302 /\nBNS 103", edge_color="#4f5666")

    # 2. Hybrid Retrieval + Cross-Encoder (x=26.5)
    draw_box(26.5, y_center, 14.0, 34, "Hybrid Retrieval + Cross-\nEncoder", edge_color="#4f5666")

    # 3. Existing Similarity Retrieval (x=44.0)
    draw_box(44.0, y_center, 15.0, 34, "Existing Similarity Retrieval\n(Highest Cosine Score)", edge_color="#4f5666")

    # 4. Parallel Stacked Boxes (x=63.5)
    y_top = 64.0
    draw_box(63.5, y_top, 16.5, 23, "Chooses Case A\n(Based Only on Highest\nText Similarity)", edge_color="#ef4444", face_color="#181315", text_color="#fca5a5", font_size=9.5)

    y_bottom = 24.0
    draw_box(63.5, y_bottom, 16.5, 23, "Misses Precedent Evolution:\nCase A was Overruled\nby Later Bench", edge_color="#ef4444", face_color="#181315", text_color="#fca5a5", font_size=9.5)

    # 5. Standard Legal LLM Reasoning (x=80.5)
    draw_box(80.5, y_center, 11.5, 34, "Standard Legal LLM\nReasoning\n(No Precedent Graph)", edge_color="#4f5666", font_size=9.5)

    # 6. Inaccurate Legal Prediction (x=93.5)
    draw_box(93.5, y_center, 9.5, 38, "Inaccurate Legal\nPrediction +\nOverruled Law\nCited  \u2718", edge_color="#ef4444", face_color="#1c1214", text_color="#fca5a5", bold=True, font_size=9.5)

    # Function to draw clean connecting arrows
    def draw_arrow(x1, y1, x2, y2, color="#71717a", rad=0.0):
        connection_style = f"arc3,rad={rad}"
        arrow = patches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            connectionstyle=connection_style,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.2,
            color=color,
            zorder=2
        )
        ax.add_patch(arrow)

    # Arrow 1 -> 2
    draw_arrow(16.5, y_center, 19.5, y_center)

    # Arrow 2 -> 3
    draw_arrow(33.5, y_center, 36.5, y_center)

    # Branching arrows from Box 3 to Top & Bottom parallel boxes
    draw_arrow(51.5, y_center + 5.0, 55.2, y_top - 2.0, rad=-0.12, color="#ef4444")
    draw_arrow(51.5, y_center - 5.0, 55.2, y_bottom + 2.0, rad=0.12, color="#ef4444")

    # Converging arrows from Top & Bottom parallel boxes into Box 5
    draw_arrow(71.8, y_top - 2.0, 74.7, y_center + 5.0, rad=-0.12, color="#ef4444")
    draw_arrow(71.8, y_bottom + 2.0, 74.7, y_center - 5.0, rad=0.12, color="#ef4444")

    # Arrow 5 -> 6
    draw_arrow(86.3, y_center, 88.7, y_center, color="#ef4444")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#202020', edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Existing pipeline horizontal diagram created successfully at {output_path}")

if __name__ == "__main__":
    create_existing_horizontal_pipeline()
