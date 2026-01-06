"""
Download BioBERT model locally for offline use
"""
import os
import sys
from pathlib import Path

def download_biobert_model():
    """Download BioBERT model using huggingface-hub"""
    try:
        # Check if huggingface-hub is installed
        import huggingface_hub
        print("✅ huggingface-hub is available")
    except ImportError:
        print("❌ huggingface-hub not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface-hub"])
        import huggingface_hub
        print("✅ huggingface-hub installed successfully")
    
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Define model path
    biobert_path = models_dir / "biobert-base-cased-v1.2"
    
    print(f"📁 Downloading BioBERT model to: {biobert_path}")
    
    try:
        # Download the model
        from huggingface_hub import snapshot_download
        
        # Download dmis-lab/biobert-base-cased-v1.2
        snapshot_download(
            repo_id="dmis-lab/biobert-base-cased-v1.2",
            local_dir=str(biobert_path),
            local_dir_use_symlinks=False
        )
        
        print("✅ BioBERT model downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading BioBERT model: {e}")
        
        # Try alternative approach with transformers
        try:
            print("🔄 Trying alternative download method...")
            from transformers import AutoTokenizer, AutoModel
            
            # This will download and cache the model
            tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
            model = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
            
            # Save to local directory
            tokenizer.save_pretrained(str(biobert_path))
            model.save_pretrained(str(biobert_path))
            
            print("✅ BioBERT model downloaded successfully using transformers!")
            return True
            
        except Exception as e2:
            print(f"❌ Alternative download method also failed: {e2}")
            return False

def verify_biobert_model():
    """Verify that BioBERT model was downloaded correctly"""
    biobert_path = Path("models") / "biobert-base-cased-v1.2"
    
    if not biobert_path.exists():
        print(f"❌ BioBERT directory not found: {biobert_path}")
        return False
    
    # Check for essential files
    essential_files = [
        "config.json",
        "pytorch_model.bin",
        "tokenizer_config.json",
        "vocab.txt"
    ]
    
    print(f"🔍 Checking for essential files in {biobert_path}:")
    all_found = True
    
    for file in essential_files:
        file_path = biobert_path / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (MISSING)")
            all_found = False
    
    return all_found

def update_config_files():
    """Update configuration files to use local BioBERT model"""
    try:
        # Update .env file
        env_file = Path(".env")
        if env_file.exists():
            content = env_file.read_text()
            # Replace EMBEDDING_MODEL line
            lines = content.splitlines()
            new_lines = []
            found_embedding = False
            
            for line in lines:
                if line.startswith("EMBEDDING_MODEL="):
                    new_lines.append("EMBEDDING_MODEL=./models/biobert-base-cased-v1.2")
                    found_embedding = True
                else:
                    new_lines.append(line)
            
            if not found_embedding:
                new_lines.append("EMBEDDING_MODEL=./models/biobert-base-cased-v1.2")
            
            env_file.write_text("\n".join(new_lines) + "\n")
            print("✅ Updated .env file to use local BioBERT model")
        
        # Update backend/config.py
        config_file = Path("backend") / "config.py"
        if config_file.exists():
            content = config_file.read_text()
            # Replace the embedding_model line
            old_line = 'embedding_model: str = Field("dmis-lab/biobert-base-cased-v1.2", env="EMBEDDING_MODEL")'
            new_line = 'embedding_model: str = Field("./models/biobert-base-cased-v1.2", env="EMBEDDING_MODEL")'
            
            if old_line in content:
                content = content.replace(old_line, new_line)
                config_file.write_text(content)
                print("✅ Updated backend/config.py to use local BioBERT model")
            else:
                print("⚠️  Could not find embedding_model line in config.py to update")
        
        return True
    except Exception as e:
        print(f"❌ Error updating config files: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BIOBERT MODEL DOWNLOAD SCRIPT")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"📂 Working directory: {project_dir}")
    
    # Download model
    print("\n📥 STEP 1: Downloading BioBERT model...")
    download_success = download_biobert_model()
    
    if download_success:
        print("\n🔍 STEP 2: Verifying downloaded model...")
        verify_success = verify_biobert_model()
        
        if verify_success:
            print("\n⚙️  STEP 3: Updating configuration files...")
            config_success = update_config_files()
            
            if config_success:
                print("\n" + "=" * 60)
                print("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
                print("✅ BioBERT model is ready for offline use")
                print("✅ Configuration files updated")
                print("\nNext steps:")
                print("1. Set TRANSFORMERS_OFFLINE=1 in your environment")
                print("2. Run: python test_biobert_offline.py")
                print("3. Start the application: python scripts/run.py")
                print("=" * 60)
            else:
                print("\n❌ Configuration update failed")
        else:
            print("\n❌ Model verification failed")
    else:
        print("\n❌ Model download failed")