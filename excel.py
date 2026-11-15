import datetime
import os

import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import points_to_pixels
from PIL import Image as PILImage

from models import AerialInspectionSurvey, PRFFeature, TreeSurvey

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "template.xlsm")
MASTER_SHEET_NAME = "T13"

# Sheets present in the raw template that are either worked examples or
# obsolete draft layouts. None of these are copied into generated output —
# only MASTER_SHEET_NAME's layout is used, once per tree.
SHEETS_TO_KEEP = {"Sheet2"}
_MASTER_WORKING_NAME = "_MASTER_TEMPLATE"

# Tree-level fields: (cell, TreeSurvey attribute name)
TREE_FIELD_CELLS = {
    "B2": "site_name",
    "F2": "licence_no",
    "B4": "tree_ref",
    "D4": "overall_suitability",
    "B6": "habitat",
    "B7": "w3w",
    "B8": "tree_species",
    "B9": "tree_alive",
    "B10": "dbh_cm",
    "B11": "tree_height_m",
    "B12": "tree_form",
    "B13": "temperature",
    "B14": "cloud_cover",
    "B15": "humidity_pct",
    "B16": "wind",
}
DATE_CELL = "B5"

# PRF row layout: row number -> PRFFeature attribute name.
# Columns D..M (1 per PRF slot, PRF n -> column 3+n) hold the values.
PRF_ROW_FIELDS = {
    21: "prf_height_m",
    22: "dph_cm",
    23: "entrance_height_cm",
    24: "entrance_width_cm",
    25: "internal_width_cm",
    26: "internal_depth_cm",
    27: "internal_height_cm",
    28: "feature_type",
    29: "aspect",
    30: "orientation",
    31: "droppings",  # bool -> "Yes"/"No"
    32: "bat_notes",
    33: "smell",
    34: "substrate",
    35: "humidity_condition",
    36: "apex_shape",
    37: "competitors",
    38: "prf_suitability",
    39: "inspection_notes_1",
    40: "inspection_notes_2",
    41: "inspection_notes_3",
}
PHOTO_ROW = 42

MIN_PRF_COL = 4  # column D
MAX_PRF_SLOTS = 10


def _prf_column(prf_number: int) -> int:
    return MIN_PRF_COL + prf_number - 1


def load_template() -> openpyxl.Workbook:
    return openpyxl.load_workbook(TEMPLATE_PATH, keep_vba=True, data_only=False)


def _clear_tree_sheet_data(ws) -> None:
    # Note: ws.cell(row, col, value=None) treats None as "no value given"
    # and leaves existing content untouched, so cells must be cleared via
    # direct .value assignment instead.
    for cell in list(TREE_FIELD_CELLS.keys()) + [DATE_CELL]:
        ws[cell] = None
    for row in list(PRF_ROW_FIELDS.keys()) + [PHOTO_ROW]:
        for col in range(MIN_PRF_COL, MIN_PRF_COL + MAX_PRF_SLOTS):
            ws.cell(row=row, column=col).value = None


def _set_tree_fields(ws, tree: TreeSurvey) -> None:
    for cell, attr in TREE_FIELD_CELLS.items():
        ws[cell] = getattr(tree, attr)
    ws[DATE_CELL] = datetime.datetime.strptime(tree.date, "%Y-%m-%d")


def _find_photo(photos_dir: str | None, tree_ref: int, prf_number: int) -> str | None:
    if photos_dir is None or not os.path.isdir(photos_dir):
        return None
    prefix = f"T{tree_ref}_PRF{prf_number}."
    for name in sorted(os.listdir(photos_dir)):
        if name.startswith(prefix):
            return os.path.join(photos_dir, name)
    return None


def _set_prf_fields(
    ws, prf: PRFFeature, tree_ref: int, photos_dir: str | None
) -> None:
    if not 1 <= prf.prf_number <= MAX_PRF_SLOTS:
        raise ValueError(f"prf_number {prf.prf_number} out of range 1-{MAX_PRF_SLOTS}")
    col = _prf_column(prf.prf_number)
    for row, attr in PRF_ROW_FIELDS.items():
        value = getattr(prf, attr)
        if attr == "droppings":
            value = "Yes" if value else "No"
        ws.cell(row=row, column=col).value = value
    # An explicit photo_path wins; otherwise fall back to an uploaded file.
    photo = prf.photo_path or _find_photo(photos_dir, tree_ref, prf.prf_number)
    if photo:
        embed_photo(ws, photo, PHOTO_ROW, col)


def embed_photo(ws, photo_path: str, row: int, col: int) -> None:
    if not os.path.isfile(photo_path):
        return

    col_letter = get_column_letter(col)
    col_dim = ws.column_dimensions[col_letter]
    row_dim = ws.row_dimensions[row]
    col_width_chars = col_dim.width or 8.43
    row_height_pts = row_dim.height or 15.0

    # Standard Excel character-width-to-pixel approximation (~7px per unit
    # plus padding for the default font), then a 5% safety margin so the
    # image never overflows the cell it's anchored in.
    max_width_px = (col_width_chars * 7 + 5) * 0.95
    max_height_px = points_to_pixels(row_height_pts) * 0.95

    with PILImage.open(photo_path) as pil_img:
        native_w, native_h = pil_img.size

    scale = min(max_width_px / native_w, max_height_px / native_h)
    target_w = max(1, int(native_w * scale))
    target_h = max(1, int(native_h * scale))

    img = XLImage(photo_path)
    img.width = target_w
    img.height = target_h
    ws.add_image(img, f"{col_letter}{row}")


def build_tree_sheet(
    wb: openpyxl.Workbook, tree: TreeSurvey, sheet_name: str, photos_dir: str | None
) -> None:
    master = wb[_MASTER_WORKING_NAME]
    ws = wb.copy_worksheet(master)
    ws.title = sheet_name

    _clear_tree_sheet_data(ws)
    _set_tree_fields(ws, tree)
    for prf in tree.prfs:
        _set_prf_fields(ws, prf, tree.tree_ref, photos_dir)


def build_excel(
    survey: AerialInspectionSurvey, output_path: str, photos_dir: str | None = None
) -> str:
    wb = load_template()

    # Free up every "T*" sheet name (the worked examples and obsolete draft
    # layouts baked into the raw template) before creating tree sheets, so a
    # tree_ref that collides with one of those names (e.g. 13) doesn't get
    # silently renamed by openpyxl's duplicate-title handling.
    master = wb[MASTER_SHEET_NAME]
    master.title = _MASTER_WORKING_NAME
    for name in list(wb.sheetnames):
        if name not in SHEETS_TO_KEEP and name != _MASTER_WORKING_NAME:
            del wb[name]

    for tree in survey.trees:
        build_tree_sheet(wb, tree, f"T{tree.tree_ref}", photos_dir)

    del wb[_MASTER_WORKING_NAME]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wb.save(output_path)
    return output_path
