import os
import re
import requests

USERNAME = "smallfoot47"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

LANG_LOGOS = {
    "JavaScript": "javascript", "TypeScript": "typescript", "Python": "python",
    "Shell": "gnubash", "C": "c", "C++": "cplusplus", "Rust": "rust",
    "Go": "go", "Java": "java", "Kotlin": "kotlin", "Swift": "swift",
    "Ruby": "ruby", "PHP": "php", "HTML": "html5", "CSS": "css3",
    "Lua": "lua", "Makefile": "cmake", "Dockerfile": "docker", "Nix": "nixos",
    "PowerShell": "powershell", "Perl": "perl", "Scala": "scala",
    "Haskell": "haskell", "Elixir": "elixir", "Zig": "zig",
}

REPO_EMOJI = {
    "Python": "🐍", "JavaScript": "🌐", "TypeScript": "🌐",
    "C": "⚙️", "C++": "⚙️", "Rust": "🦀", "Shell": "💻",
    "Go": "🐹", "Java": "☕", "Ruby": "💎",
}

def get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}

def fetch_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            params={"per_page": 100, "page": page},
            headers=get_headers(),
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def fetch_languages(repos):
    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        r = requests.get(repo["languages_url"], headers=get_headers())
        if r.ok:
            for lang, count in r.json().items():
                totals[lang] = totals.get(lang, 0) + count
    return totals

def build_language_badges(lang_totals, top_n=8):
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    badges = []
    for lang, _ in sorted_langs:
        logo = LANG_LOGOS.get(lang, lang.lower().replace("+", "p").replace(" ", "").replace("#", "sharp"))
        encoded_name = lang.replace("+", "%2B").replace(" ", "_")
        badges.append(
            f"![{lang}](https://img.shields.io/badge/{encoded_name}-0d1117"
            f"?style=for-the-badge&logo={logo}&logoColor=4DC377)"
        )
    return "\n".join(badges)

def build_projects_table(repos, top_n=3):
    candidates = sorted(
        [r for r in repos if not r.get("fork") and r.get("description")],
        key=lambda x: (x.get("stargazers_count", 0), x.get("pushed_at", "")),
        reverse=True,
    )[:top_n]

    rows = [
        "| Project | Description | Stack |",
        "|---|---|---|",
    ]
    for repo in candidates:
        lang = repo.get("language") or ""
        emoji = REPO_EMOJI.get(lang, "🔒")
        desc = (repo.get("description") or "").replace("|", "\\|")[:80]
        if len(repo.get("description") or "") > 80:
            desc += "…"
        stack = f"`{lang}`" if lang else ""
        rows.append(
            f"| [{emoji} {repo['name']}](https://github.com/{USERNAME}/{repo['name']}) "
            f"| {desc} | {stack} |"
        )
    return "\n".join(rows)

def replace_section(content, marker, new_body):
    pattern = rf"(<!-- {marker}_START -->).*?(<!-- {marker}_END -->)"
    replacement = rf"\g<1>\n{new_body}\n\g<2>"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def main():
    print("Fetching repos…")
    repos = fetch_repos()
    print(f"  Found {len(repos)} repos")

    print("Fetching language data…")
    lang_totals = fetch_languages(repos)
    print(f"  Found {len(lang_totals)} languages")

    lang_badges = build_language_badges(lang_totals)
    projects_table = build_projects_table(repos)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = replace_section(content, "LANGUAGES", lang_badges)
    content = replace_section(content, "PROJECTS", projects_table)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("README updated.")

if __name__ == "__main__":
    main()
