"""
Script to generate the vertical flowchart for CiteJustice LexGraphFormer Pipeline.
Exact replica of the user's diagram transposed to an elegant vertical layout.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

import os

def create_vertical_pipeline(output_path=None):
    if output_path is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(root_dir, "Images", "Pipelines", "CiteJustice_Proposed_Pipeline_Vertical.png")
    # Figure dimensions: vertical layout (width 9 inches, height 14.5 inches)
    fig, ax = plt.subplots(figsize=(9, 14.5))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Function to draw styled dark node box
    def draw_box(x, y, w, h, text, edge_color="#555555", face_color="#121212", text_color="#ffffff", bold=False, font_size=12):
        box = patches.FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="square,pad=0.5",
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
            linespacing=1.35,
            family="sans-serif",
            zorder=4
        )
        return box

    # Title at the top - styled container card for 100% visibility on both light & dark backgrounds
    draw_box(
        50, 92.5, 62, 7.2,
        "CiteJustice\nLexGraphFormer Pipeline\n(Precedent-Aware)",
        edge_color="#3b82f6",
        face_color="#0f172a",
        text_color="#93c5fd",
        bold=True,
    )

    # Node coordinates (vertical flow from y=80 down to y=12)
    # 1. New Case Facts
    box1_y = 79.5
    draw_box(50, box1_y, 60, 6.8, "New Case Facts: IPC 302 /\nBNS 103", edge_color="#4f5666")

    # 2. Hybrid Retrieval + Cross-Encoder
    box2_y = 66.5
    draw_box(50, box2_y, 60, 6.8, "Hybrid Retrieval + Cross-\nEncoder", edge_color="#4f5666")

    # 3. Dynamic Precedent Evolution Graph - DPEG
    box3_y = 53.5
    draw_box(50, box3_y, 60, 6.8, "Dynamic Precedent\nEvolution Graph - DPEG", edge_color="#4f5666")

    # 4. Two Parallel Branch Boxes (Side-by-side)
    branch_y = 39.5
    # Branch A (Left): Detects Case A Overruled
    draw_box(29, branch_y, 38, 7.5, "Detects: Case A Overruled\n(-3 penalty)", edge_color="#ef4444", face_color="#181315", text_color="#fca5a5")

    # Branch B (Right): Identifies Case B & C
    draw_box(71, branch_y, 38, 7.5, "Identifies: Case B\n(Followed) & Case C\n(Distinguished)", edge_color="#10b981", face_color="#111815", text_color="#86efac")

    # 5. Graph Transformer + Legal LLM Reasoning
    box5_y = 25.5
    draw_box(50, box5_y, 62, 6.8, "Graph Transformer + Legal\nLLM Reasoning", edge_color="#4f5666")

    # 6. Valid Legal Prediction + IRAC Report
    box6_y = 12.0
    draw_box(50, box6_y, 66, 7.8, "Valid Legal Prediction +\nIRAC Report + Precedent\nAuthority Score  \u2714", edge_color="#d4af37", face_color="#1a1811", text_color="#fef08a", bold=True)

    # Function to draw clean connecting arrows
    def draw_arrow(x1, y1, x2, y2, color="#71717a", rad=0.0):
        connection_style = f"arc3,rad={rad}"
        arrow = patches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            connectionstyle=connection_style,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.3,
            color=color,
            zorder=2
        )
        ax.add_patch(arrow)

    # Arrow 1 -> 2
    draw_arrow(50, box1_y - 3.5, 50, box2_y + 3.5)

    # Arrow 2 -> 3
    draw_arrow(50, box2_y - 3.5, 50, box3_y + 3.5)

    # Branching arrows from Box 3 to Left & Right branch boxes
    draw_arrow(42, box3_y - 3.5, 29, branch_y + 3.8, rad=0.15, color="#ef4444")
    draw_arrow(58, box3_y - 3.5, 71, branch_y + 3.8, rad=-0.15, color="#10b981")

    # Converging arrows from Left & Right branch boxes into Box 5
    draw_arrow(29, branch_y - 3.8, 42, box5_y + 3.5, rad=-0.15, color="#ef4444")
    draw_arrow(71, branch_y - 3.8, 58, box5_y + 3.5, rad=0.15, color="#10b981")

    # Arrow 5 -> 6
    draw_arrow(50, box5_y - 3.5, 50, box6_y + 3.9, color="#d4af37")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, transparent=True, bbox_inches='tight')
    plt.close()
    print(f"Vertical diagram created successfully at {output_path}")

if __name__ == "__main__":
    create_vertical_pipeline()
