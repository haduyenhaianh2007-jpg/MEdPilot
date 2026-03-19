from pathlib import Path

image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff'}

parent_folder = r"C:\Users\Admin\Downloads\DermNet_Data_Vietnamese-20260317T010231Z-1-001\DermNet_Data_Vietnamese"  # Thay bằng đường dẫn cha chứa 110 folder

deleted_count = 0
total_size = 0

# Duyệt qua tất cả folder con
for folder in Path(parent_folder).iterdir():
    if folder.is_dir():
        print(f"\n📂 Xử lý folder: {folder.name}")
        
        # Tìm và xóa ảnh trong folder này
        for file in folder.rglob("*"):
            if file.is_file() and file.suffix.lower() in image_extensions:
                try:
                    size = file.stat().st_size
                    file.unlink()
                    print(f"  ✓ Xóa: {file.name}")
                    deleted_count += 1
                    total_size += size
                except Exception as e:
                    print(f"  ✗ Lỗi: {e}")

print(f"\n{'='*60}")
print(f"✓ Hoàn tất!")
print(f"   Tổng file xóa: {deleted_count}")
print(f"   Tổng dung lượng giải phóng: {total_size / (1024**2):.2f} MB")
print(f"{'='*60}")