import zipfile
import os

def zip_project(output_filename='deploy.zip'):
    exclude_dirs = {'venv', '.git', '__pycache__', '.idea', '.vscode', 'node_modules'}
    exclude_extensions = {'.pyc', '.pyo', '.pyd', '.zip'}
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_extensions):
                    continue
                if file == output_filename:
                    continue
                    
                file_path = os.path.join(root, file)
                # Archive name should be relative to project root
                arcname = os.path.relpath(file_path, '.')
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname)

if __name__ == '__main__':
    print("Zipping project...")
    zip_project()
    print("Done! Created deploy.zip")
