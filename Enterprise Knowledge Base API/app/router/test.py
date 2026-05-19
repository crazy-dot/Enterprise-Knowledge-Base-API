from pathlib import  Path

base = Path(__file__).resolve().parent.parent.parent
upload_dir = base / "files"
upload_dir.mkdir(parents=True, exist_ok=True)
print(base)


file_path = upload_dir/'Customer Support SOPs/Enterprise_Knowledge_Base_Implementation_Blueprint.pdf'
file_size = (Path(file_path).stat().st_size)/1000
print(round(file_size, 2))