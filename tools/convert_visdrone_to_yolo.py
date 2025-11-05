# tools/convert_visdrone_to_yolo.py
import os, shutil, json
from pathlib import Path
from PIL import Image
from tqdm import tqdm

"""
Konvertiert VisDrone-Detection-Labels in YOLOv8-Format.
Ordnerstruktur: data/visdrone/{annotations, images, labels}
"""

# Mapping (reduziert auf relevante Klassen)
MAP = {
    1: 0,  # pedestrian -> person
    2: 0,  # people -> person
    3: 1,  # bicycle
    4: 2,  # car
    5: 2,  # van -> car
    6: 3,  # truck
    9: 4,  # bus
    10: 5  # motor
}

def convert_split(src_img_dir, src_anno_dir, dst_img_dir, dst_lbl_dir):
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    img_files = sorted([p for p in Path(src_img_dir).glob("*.jpg")])
    for img_path in tqdm(img_files, desc=f"Converting {src_img_dir.name}"):
        label_name = img_path.stem + ".txt"
        anno_path = Path(src_anno_dir) / label_name
        with Image.open(img_path) as im:
            w, h = im.size
        lines_out = []
        if anno_path.exists():
            with open(anno_path, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) < 8:
                        continue
                    xmin, ymin, bw, bh = map(float, parts[:4])
                    category = int(parts[5])
                    if category in MAP:
                        cls = MAP[category]
                        x_c = (xmin + bw / 2) / w
                        y_c = (ymin + bh / 2) / h
                        ww = bw / w
                        hh = bh / h
                        if ww > 0 and hh > 0:
                            lines_out.append(f"{cls} {x_c:.6f} {y_c:.6f} {ww:.6f} {hh:.6f}")
        shutil.copy2(img_path, dst_img_dir / img_path.name)
        with open(dst_lbl_dir / label_name, "w") as fo:
            fo.write("\n".join(lines_out))

if __name__ == "__main__":
    root = Path("data/visdrone")
    train_img = root / "images"
    train_ano = root / "annotations"
    val_img   = root / "images"     # hier nutzen wir denselben Split (Demo)
    val_ano   = root / "annotations"

    out_root = Path("data/visdrone_yolo")
    (out_root / "images/train").mkdir(parents=True, exist_ok=True)
    (out_root / "images/val").mkdir(parents=True, exist_ok=True)
    (out_root / "labels/train").mkdir(parents=True, exist_ok=True)
    (out_root / "labels/val").mkdir(parents=True, exist_ok=True)

    convert_split(train_img, train_ano, out_root / "images/train", out_root / "labels/train")
    convert_split(val_img, val_ano, out_root / "images/val", out_root / "labels/val")

    data_yaml = {
        "path": str(out_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {
            0: "person",
            1: "bicycle",
            2: "car",
            3: "truck",
            4: "bus",
            5: "motor"
        }
    }
    with open(out_root / "data.yaml", "w") as f:
        f.write(json.dumps(data_yaml, indent=2))

    print("✓ Conversion done. YOLO dataset at:", out_root.resolve())

