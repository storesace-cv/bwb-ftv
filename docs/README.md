# Overlay Naming Scheme

This project uses a structured naming scheme for identifying overlay segments:

- **Blocks**: `B{n}.C{n}` denotes root blocks (e.g., `B1.C1`, `B2.C2`).
- **Horizontal subdivisions**: `.A` for the left section and `.B` for the right.
- **Vertical subdivisions**: `.1`, `.2`, etc.
- **Order**: Start with the block and cell identifier,
  then alternate horizontal and vertical markers as needed (e.g., `B1.C1.A.2.B`).

Overlays can obscure the underlying UI, so these names should only be visible when the **Overlays** toggle is switched ON.

