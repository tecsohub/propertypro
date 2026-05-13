from pathlib import Path
import tempfile

import ezdxf
from ezdxf.addons import odafc
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration, HatchPolicy, TextPolicy
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from pypdf import PdfReader


def configure_odafc_path():
    """Configure ODA executable path when installed in a versioned folder."""
    if odafc.is_installed():
        return

    search_roots = [
        Path("C:/Program Files/ODA"),
        Path("C:/Program Files (x86)/ODA"),
    ]

    candidates = []
    for root in search_roots:
        if root.exists():
            candidates.extend(root.glob("ODAFileConverter*/ODAFileConverter.exe"))

    if candidates:
        # Use the highest version-like folder name when multiple candidates exist.
        best_match = sorted(candidates, key=lambda path: path.parent.name)[-1]
        ezdxf.options.set("odafc-addon", "win_exec_path", str(best_match))


def load_cad_document(cad_path):
    """Load a CAD document, converting DWG to a temporary DXF first if needed."""
    source_path = Path(cad_path)
    suffix = source_path.suffix.lower()

    if suffix == ".dwg":
        configure_odafc_path()
        if not odafc.is_installed():
            raise RuntimeError(
                "ODA File Converter is not installed. Install it first, then rerun this script."
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dxf = Path(temp_dir) / f"{source_path.stem}.dxf"
            odafc.convert(source_path, temp_dxf, replace=True)
            return ezdxf.readfile(temp_dxf)

    return ezdxf.readfile(source_path)


def normalize_text_styles(doc):
    """Replace SHX style fonts with a TrueType fallback for reliable PDF text rendering."""
    fallback_font = "arial.ttf"
    for style in doc.styles:
        font_name = (style.dxf.font or "").lower()
        if font_name.endswith(".shx") or font_name == "":
            style.dxf.font = fallback_font


def ensure_dimension_geometry(doc):
    """Generate missing anonymous geometry blocks for DIMENSION entities."""
    for entity in doc.modelspace().query("DIMENSION"):
        geometry_name = entity.dxf.get("geometry", "")
        if not geometry_name or geometry_name not in doc.blocks:
            entity.render()


def flatten_insert_entities(entities, max_depth=5, depth=0):
    """Recursively expand INSERT entities into virtual primitives."""
    for entity in entities:
        if entity.dxftype() == "INSERT" and depth < max_depth:
            yield from flatten_insert_entities(entity.virtual_entities(), max_depth=max_depth, depth=depth + 1)
        else:
            yield entity


def _boost_text_size(entity, scale=1.8):
    """Increase text size for readability in exported PDFs."""
    if entity.dxftype() == "TEXT" and entity.dxf.hasattr("height"):
        entity.dxf.height = max(float(entity.dxf.height) * scale, 1.8)
    elif entity.dxftype() == "MTEXT" and entity.dxf.hasattr("char_height"):
        entity.dxf.char_height = max(float(entity.dxf.char_height) * scale, 1.8)
    return entity


def build_render_entities(layout):
    """Render dimensions in two passes so labels stay visible on top."""
    base_entities = []
    dimension_text_entities = []

    for entity in layout:
        if entity.dxftype() == "DIMENSION":
            for virtual in flatten_insert_entities(entity.virtual_entities()):
                if virtual.dxftype() in {"TEXT", "MTEXT"}:
                    dimension_text_entities.append(_boost_text_size(virtual))
                else:
                    base_entities.append(virtual)
        else:
            base_entities.append(entity)

    yield from base_entities
    yield from dimension_text_entities


def get_reference_figure_size(default_size=(11, 8.5)):
    """Use PROJECT MAP.pdf page dimensions as plotting reference when available."""
    reference_pdf = Path("PROJECT MAP.pdf")
    if not reference_pdf.exists():
        return default_size

    try:
        page = PdfReader(str(reference_pdf)).pages[0]
        width_in = float(page.mediabox.width) / 72.0
        height_in = float(page.mediabox.height) / 72.0
        if width_in > 0 and height_in > 0:
            return (width_in, height_in)
    except Exception:
        pass

    return default_size


def cad_to_pdf(cad_path, pdf_path, resolution=1200):
    """
    Converts a DWG/DXF file to a high-resolution PDF.

    Args:
        cad_path (str): Path to the input DWG or DXF file.
        pdf_path (str): Path to the output PDF file.
        resolution (int): DPI for rasterized elements in the PDF.
    """
    try:
        doc = load_cad_document(cad_path)
        normalize_text_styles(doc)
        ensure_dimension_geometry(doc)
        modelspace = doc.modelspace()

        figure = plt.figure(figsize=get_reference_figure_size(), dpi=resolution)
        axes = figure.add_axes([0, 0, 1, 1])
        axes.set_aspect("equal")
        axes.axis("off")

        context = RenderContext(doc)
        backend = MatplotlibBackend(axes)
        config = Configuration(
            color_policy=ColorPolicy.COLOR_SWAP_BW,
            background_policy=BackgroundPolicy.WHITE,
            text_policy=TextPolicy.FILLING,
            hatch_policy=HatchPolicy.NORMAL,
        )
        frontend = Frontend(context, backend, config=config)
        frontend.draw_entities(build_render_entities(modelspace))
        backend.finalize()

        axes.autoscale_view()
        axes.margins(0.02)
        figure.savefig(pdf_path, format="pdf", dpi=resolution)
        plt.close(figure)
        print(f"Successfully converted {cad_path} to {pdf_path}")

    except FileNotFoundError:
        print(f"File not found: {cad_path}")
    except RuntimeError as error:
        print(str(error))
    except ezdxf.DXFStructureError:
        print(f"Invalid or corrupt CAD file: {cad_path}")
    except IOError:
        print(f"Could not write file: {pdf_path}")

if __name__ == "__main__":
    cad_file = input("Enter the path to the DWG or DXF file: ")
    pdf_file = input("Enter the path for the output PDF file: ")

    try:
        dpi = int(input("Enter the desired resolution (DPI), default is 1200: ") or 1200)
    except ValueError:
        dpi = 1200
        print("Invalid resolution, using default 1200 DPI.")

    cad_to_pdf(cad_file, pdf_file, resolution=dpi)
