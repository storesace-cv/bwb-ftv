# Overlay Naming Scheme

This project uses a structured naming scheme for identifying overlay segments:

- **Blocks**: `B{n}` denote top-level blocks (e.g., `B1`, `B2`).
- **Cells**: `C{n}` denotes root cells (e.g., `C1`, `C2`). Cell names are prefixed by their parent
  block, and each block resets cell numbering to 1 (e.g., `B1.C1`, `B2.C1`, `B3.C1`). Block `B3`
  begins with cell `B3.C1`, not `B3.C3`.
- **Horizontal subdivisions**: `.A` for the left section and `.B` for the right.
- **Vertical subdivisions**: `.1`, `.2`, etc.
- **Order**: Start with the block identifier followed by the cell name, then alternate horizontal and vertical markers as needed (e.g., `B1.C1.A.2.B`).

![Example of the `B1.C1.A.2.B` naming](b1-c1-a2b-diagram.svg)

Overlays can obscure the underlying UI, so these names should only be visible when the **Overlays** toggle is switched ON. Click the **Overlays** button or press **Ctrl+D** in the application to toggle these labels.

