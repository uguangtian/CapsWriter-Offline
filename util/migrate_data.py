import shutil
import os
import re
from pathlib import Path
# Add parent directory to sys.path to allow importing util
import sys
sys.path.append(str(Path(__file__).parent.parent))

from util.config import ClientConfig, ModelPaths

def migrate():
    # Calculate project root based on this file's location: .../util/migrate_data.py -> .../
    project_root = Path(__file__).parent.parent
    
    # Target paths
    new_results_path = Path(ClientConfig.transcription_result_path).expanduser()
    new_audio_path = Path(ClientConfig.audio_storage_path).expanduser()
    new_models_path = Path(ModelPaths.model_dir).expanduser()
    
    print(f"Migrating data...")
    print(f"From: {project_root}")
    print(f"To Results: {new_results_path}")
    print(f"To Audio: {new_audio_path}")
    print(f"To Models: {new_models_path}")
    
    # Ensure target root directories exist
    new_results_path.mkdir(parents=True, exist_ok=True)
    new_audio_path.mkdir(parents=True, exist_ok=True)
    new_models_path.mkdir(parents=True, exist_ok=True)

    # 0. Move Models directory contents
    src_models_dir = project_root / "models"
    if src_models_dir.exists() and src_models_dir.is_dir():
        print(f"Processing models directory: {src_models_dir}")
        for item in src_models_dir.iterdir():
            target_item = new_models_path / item.name
            if target_item.exists():
                print(f"Skipped {item} (already exists at {target_item})")
                continue
            try:
                shutil.move(str(item), str(target_item))
                print(f"Moved {item} to {target_item}")
            except Exception as e:
                print(f"Failed to move {item}: {e}")
        # Try to remove empty models dir
        try:
            if not any(src_models_dir.iterdir()):
                src_models_dir.rmdir()
                print(f"Removed empty directory: {src_models_dir}")
        except OSError as e:
            print(f"Could not remove {src_models_dir}: {e}")

    # Iterate over directories in project root
    for year_dir in project_root.iterdir():
        if not year_dir.is_dir():
            continue
        
        # Check if it looks like a year directory (4 digits)
        if not re.match(r'^\d{4}$', year_dir.name):
            continue
            
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            
            # Check if it looks like a month directory (2 digits)
            if not re.match(r'^\d{2}$', month_dir.name):
                continue
                
            # Found a data directory: project_root/YYYY/MM
            print(f"Processing {year_dir.name}/{month_dir.name}...")
            
            # 1. Move Markdown files
            target_md_dir = new_results_path / year_dir.name / month_dir.name
            target_md_dir.mkdir(parents=True, exist_ok=True)
            
            for item in month_dir.iterdir():
                if item.is_file() and item.suffix.lower() == '.md':
                    # Move .md file
                    target_file = target_md_dir / item.name
                    if not target_file.exists():
                        shutil.move(str(item), str(target_file))
                        print(f"Moved {item.name} to {target_file}")
                    else:
                        print(f"Skipped {item.name} (already exists)")
            
            # 2. Move Audio files (in assets)
            assets_dir = month_dir / "assets"
            if assets_dir.exists() and assets_dir.is_dir():
                target_assets_dir = new_audio_path / year_dir.name / month_dir.name / "assets"
                target_assets_dir.mkdir(parents=True, exist_ok=True)
                
                for item in assets_dir.iterdir():
                    if item.is_file():
                        # Move audio file (and any other file in assets)
                        target_file = target_assets_dir / item.name
                        if not target_file.exists():
                            shutil.move(str(item), str(target_file))
                            print(f"Moved {item.name} to {target_file}")
                        else:
                            print(f"Skipped {item.name} (already exists)")
                
                # Try to remove empty assets dir
                try:
                    if not any(assets_dir.iterdir()):
                        assets_dir.rmdir()
                        print(f"Removed empty directory: {assets_dir}")
                except OSError as e:
                    print(f"Could not remove {assets_dir}: {e}")

            # Try to remove empty month dir
            try:
                if not any(month_dir.iterdir()):
                    month_dir.rmdir()
                    print(f"Removed empty directory: {month_dir}")
            except OSError as e:
                print(f"Could not remove {month_dir}: {e}")
        
        # Try to remove empty year dir
        try:
            if not any(year_dir.iterdir()):
                year_dir.rmdir()
                print(f"Removed empty directory: {year_dir}")
        except OSError as e:
            print(f"Could not remove {year_dir}: {e}")

if __name__ == "__main__":
    migrate()
