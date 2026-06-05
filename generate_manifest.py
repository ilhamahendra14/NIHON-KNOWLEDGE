#!/usr/bin/env python3
"""
Generate manifest.json for Knowledge files

Usage:
    python generate_manifest.py --knowledge-dir ./KNOWLEDGE --output ./manifest.json --repo-url https://github.com/user/repo

This scans all files in KNOWLEDGE directory, computes SHA256 hashes,
and generates a manifest.json file for version control and update checking.
"""

import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_git_remote_url() -> str | None:
     """Auto-detect GitHub repo URL from git remote."""
     try:
         result = subprocess.run(
             ["git", "remote", "get-url", "origin"],
             capture_output=True,
             text=True,
             timeout=5
         )
         if result.returncode == 0:
             url = result.stdout.strip()
             # Convert git@github.com:user/repo.git to https URL if needed
             if url.startswith("git@github.com:"):
                 url = url.replace("git@github.com:", "https://github.com/")
             # Remove .git suffix
             if url.endswith(".git"):
                 url = url[:-4]
             return url
     except Exception:
         pass
     return None


def generate_manifest(knowledge_dir: Path, repo_url: str, branch: str = "main") -> dict:
    """
    Generate manifest by scanning all files in knowledge_dir.
    
    Args:
        knowledge_dir: Path to KNOWLEDGE folder
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        branch: Git branch name (default: main)
    
    Returns:
        Manifest dictionary
    """
    if not knowledge_dir.is_dir():
        raise ValueError(f"Knowledge directory not found: {knowledge_dir}")

    files = {}
    
    # Scan all files recursively
    for file_path in knowledge_dir.rglob("*"):
        if file_path.is_file():
            # Skip manifest.json itself
            if file_path.name == "manifest.json":
                continue
            
            # Relative path for manifest
            rel_path = str(file_path.relative_to(knowledge_dir)).replace("\\", "/")
            
            # Compute hash and size
            sha256 = compute_sha256(file_path)
            size = file_path.stat().st_size
            
            # Construct raw GitHub URL
            raw_url = f"{repo_url.rstrip('/')}/raw/{branch}/KNOWLEDGE/{rel_path}"
            
            files[rel_path] = {
                "sha256": sha256,
                "size": size,
                "url": raw_url
            }
            
            print(f"✓ {rel_path:50} ({size:>10} bytes) {sha256[:16]}...")

    manifest = {
        "version": datetime.now().strftime("%Y.%m.%d"),  # Version as date
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "files": files
    }

    return manifest


def main():
     parser = argparse.ArgumentParser(
         description="Generate manifest.json for Knowledge files",
         epilog="If --repo-url is not provided, it will auto-detect from git remote."
     )
     parser.add_argument("--knowledge-dir", type=Path, default=Path("./KNOWLEDGE"),
                        help="Path to KNOWLEDGE directory (default: ./KNOWLEDGE)")
     parser.add_argument("--output", type=Path, default=None,
                        help="Output manifest.json path (default: KNOWLEDGE/manifest.json)")
     parser.add_argument("--repo-url", type=str, default=None,
                        help="GitHub repository URL (optional, auto-detects from git)")
     parser.add_argument("--branch", type=str, default="main",
                        help="Git branch name (default: main)")

     args = parser.parse_args()

     # Auto-detect repo URL from git if not provided
     repo_url = args.repo_url
     if not repo_url:
         print("🔍 Auto-detecting repository URL from git...")
         repo_url = get_git_remote_url()
         if repo_url:
             print(f"✓ Detected: {repo_url}")
         else:
             print("❌ Could not auto-detect repository URL.")
             print("Please provide --repo-url or ensure you're in a git repository.")
             exit(1)

     # Auto-set output path to KNOWLEDGE/manifest.json if not provided
     if args.output is None:
         args.output = args.knowledge_dir / "manifest.json"

     print(f"📋 Generating manifest for: {args.knowledge_dir}")
     print(f"📍 Repository: {repo_url}")
     print(f"📂 Output: {args.output}")
     print()

     try:
         manifest = generate_manifest(args.knowledge_dir, repo_url, args.branch)
         
         # Save manifest
         args.output.parent.mkdir(parents=True, exist_ok=True)
         with open(args.output, "w", encoding="utf-8") as f:
             json.dump(manifest, f, indent=2)
         
         print()
         print(f"✅ Manifest generated successfully!")
         print(f"📁 Saved to: {args.output}")
         print(f"📦 Total files: {len(manifest['files'])}")
         print(f"📅 Version: {manifest['version']}")
         print()
         print("📝 Next steps:")
         print("  1. Commit manifest.json to git")
         print("  2. Push to GitHub: git push origin main")
         print()
         print("Manifest URL:")
         print(f"  {repo_url}/raw/{args.branch}/KNOWLEDGE/manifest.json")
         
     except Exception as e:
         print(f"❌ Error: {e}")
         exit(1)


if __name__ == "__main__":
    main()
