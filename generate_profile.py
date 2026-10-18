import os
import datetime
import requests

def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fetch_github_stats(username="gokula-nandhan"):
    print(f"Fetching GitHub stats for {username}...")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # 1. Resolve authentication token (GH_PAT -> GITHUB_TOKEN -> ACCESS_TOKEN -> local gh auth token)
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN")
    if not token:
        try:
            import subprocess
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            token = None

    if token:
        headers["Authorization"] = f"token {token}"
        print("Using GitHub token for authentication.")

    # Defaults / Fallbacks
    repos = 15
    stars = 1
    followers = 3
    contributed = 7
    total_contributions = 122
    commit_contributions = 17
    restricted_contributions = 83
    prs = 6
    reviews = 1
    issues = 0
    search_commits = 325

    # 2. Query GitHub GraphQL API (primary source for accurate contributions & repo counts)
    gql_query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: [OWNER]) {
          totalCount
          nodes {
            stargazerCount
          }
        }
        followers {
          totalCount
        }
        repositoriesContributedTo(first: 100) {
          totalCount
        }
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
          totalCommitContributions
          restrictedContributionsCount
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """

    graphql_success = False
    if token:
        try:
            gql_res = requests.post(
                "https://api.github.com/graphql",
                json={"query": gql_query, "variables": {"login": username}},
                headers=headers,
                timeout=10
            )
            if gql_res.status_code == 200:
                resp_json = gql_res.json()
                data = resp_json.get("data", {}).get("user")
                if data:
                    repos = data.get("repositories", {}).get("totalCount", repos)
                    repo_nodes = data.get("repositories", {}).get("nodes", [])
                    stars = sum(n.get("stargazerCount", 0) for n in repo_nodes)
                    followers = data.get("followers", {}).get("totalCount", followers)
                    contributed = data.get("repositoriesContributedTo", {}).get("totalCount", contributed)

                    cc = data.get("contributionsCollection", {})
                    total_contributions = cc.get("contributionCalendar", {}).get("totalContributions", total_contributions)
                    commit_contributions = cc.get("totalCommitContributions", commit_contributions)
                    restricted_contributions = cc.get("restrictedContributionsCount", restricted_contributions)
                    prs = cc.get("totalPullRequestContributions", prs)
                    reviews = cc.get("totalPullRequestReviewContributions", reviews)
                    issues = cc.get("totalIssueContributions", issues)
                    graphql_success = True
                    print(f"GraphQL success: {repos} repos, {stars} stars, {followers} followers, {total_contributions} contributions ({prs} PRs, {reviews} reviews).")
        except Exception as e:
            print("Error querying GitHub GraphQL API:", e)

    # 3. Fallback to REST API if GraphQL was unsuccessful
    if not graphql_success:
        print("Falling back to GitHub REST API endpoints...")
        try:
            user_res = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=5)
            if user_res.status_code == 200:
                user_data = user_res.json()
                repos = user_data.get("public_repos", repos)
                followers = user_data.get("followers", followers)
        except Exception as e:
            print("Error fetching user metadata:", e)

        try:
            repos_res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=5)
            if repos_res.status_code == 200:
                repos_data = repos_res.json()
                if isinstance(repos_data, list):
                    stars = sum(r.get("stargazers_count", 0) for r in repos_data)
        except Exception as e:
            print("Error fetching repositories details:", e)

    # 4. Search all-time public commit count across repos
    try:
        commit_headers = headers.copy()
        commit_headers["Accept"] = "application/vnd.github.cloak-preview+json"
        commit_res = requests.get(f"https://api.github.com/search/commits?q=author:{username}", headers=commit_headers, timeout=6)
        if commit_res.status_code == 200:
            commit_data = commit_res.json()
            search_commits = commit_data.get("total_count", search_commits)
    except Exception as e:
        print("Error searching commits count:", e)

    # Total all-time commits combine public search commits with restricted/private commits
    commits = max(search_commits + restricted_contributions, commit_contributions + restricted_contributions, 325)
    commits_year = commit_contributions + restricted_contributions

    # Format human-friendly contribution labels
    pr_label = f"{prs} PRs" if prs != 1 else "1 PR"
    review_label = f"{reviews} Reviews" if reviews != 1 else "1 Review"
    commit_year_label = f"{commits_year} Commits" if commits_year != 1 else "1 Commit"

    return {
        "repos": repos,
        "followers": followers,
        "stars": stars,
        "commits": commits,
        "contributed": contributed,
        "contributions": total_contributions,
        "commits_year": commits_year,
        "prs": prs,
        "reviews": reviews,
        "pr_label": pr_label,
        "review_label": review_label,
        "commit_year_label": commit_year_label
    }

def generate_svgs():
    # Escape and format the ASCII name "gokula nandhan"
    ascii_name_lines = [
        "                __         __                               ____              ",
        "   ____ _____  / /____  __/ /___ _   ____  ____ _____  ____/ / /_  ____ _____ ",
        "  / __ `/ __ \\/ //_/ / / / / __ `/  / __ \\/ __ `/ __ \\/ __  / __ \\/ __ `/ __ \\",
        " / /_/ / /_/ / ,< / /_/ / / /_/ /  / / / / /_/ / / / / /_/ / / / / /_/ / / / /",
        " \\__, /\\____/_/|_|\\__,_/_/\\__,_/  /_/ /_/\\__,_/_/ /_/\\__,_/_/ /_/\\__,_/_/ /_/ ",
        "/____/"
    ]
    ascii_name_escaped = [xml_escape(line) for line in ascii_name_lines]
    
    ascii_name_svg = ""
    for i, line in enumerate(ascii_name_escaped):
        if i == 0:
            ascii_name_svg += f'<tspan x="35" dy="0">{line}</tspan>'
        else:
            ascii_name_svg += f'\n      <tspan x="35" dy="10">{line}</tspan>'

    # Fetch live GitHub metrics
    stats = fetch_github_stats("gokula-nandhan")
    
    # Format current date
    now = datetime.datetime.now()
    date_str = now.strftime("%d %b %Y, %H:%M") + " IST"
    
    # Dark Mode SVG Template
    dark_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 545" width="950" height="545">
  <defs>
    <style>
      .terminal {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
        font-size: 13px;
        fill: #c9d1d9;
      }}
      .bold {{ font-weight: bold; }}
      .title {{ fill: #8b949e; font-size: 13px; }}
      .prompt {{ fill: #3fb950; }}
      .path {{ fill: #58a6ff; }}
      .command {{ fill: #c9d1d9; }}
      .ascii-name {{
        fill: #58a6ff;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
        font-size: 7.8px;
        font-weight: bold;
        letter-spacing: 0;
        word-spacing: 0;
      }}
      .key {{ fill: #ffbd2e; }}
      .section {{ fill: #8b949e; font-weight: bold; }}
      .value {{ fill: #c9d1d9; }}
      .link {{ fill: #58a6ff; }}
      .add {{ fill: #3fb950; }}
      .del {{ fill: #ff7b72; }}
      .ascii {{ fill: #bc8cff; font-size: 11.5px; letter-spacing: 0.5px; }}
      .cursor {{ fill: #3fb950; animation: blink 1s step-end infinite; }}
      .cursor-cmd1 {{ fill: #3fb950; animation: blink 1s step-end infinite, hide-cursor 0s forwards 1.3s; }}
      @keyframes blink {{
        50% {{ fill: transparent; }}
      }}
      @keyframes hide-cursor {{
        to {{ visibility: hidden; }}
      }}
      
      /* Staggered Telegraph Transitions */
      .reveal-1 {{ opacity: 0; animation: printLine 0.01s forwards 1.3s; }}
      .reveal-2 {{ opacity: 0; animation: printLine 0.01s forwards 1.42s; }}
      .reveal-3 {{ opacity: 0; animation: printLine 0.01s forwards 1.54s; }}
      .reveal-4 {{ opacity: 0; animation: printLine 0.01s forwards 1.66s; }}
      .reveal-5 {{ opacity: 0; animation: printLine 0.01s forwards 1.78s; }}
      .reveal-6 {{ opacity: 0; animation: printLine 0.01s forwards 1.9s; }}
      .reveal-7 {{ opacity: 0; animation: printLine 0.01s forwards 2.02s; }}
      .reveal-8 {{ opacity: 0; animation: printLine 0.01s forwards 2.14s; }}
      .reveal-9 {{ opacity: 0; animation: printLine 0.01s forwards 2.26s; }}
      .reveal-10 {{ opacity: 0; animation: printLine 0.01s forwards 2.38s; }}
      .reveal-11 {{ opacity: 0; animation: printLine 0.01s forwards 2.5s; }}
      .reveal-12 {{ opacity: 0; animation: printLine 0.01s forwards 2.62s; }}
      .reveal-13 {{ opacity: 0; animation: printLine 0.01s forwards 2.74s; }}
      .reveal-14 {{ opacity: 0; animation: printLine 0.01s forwards 2.86s; }}
      .reveal-15 {{ opacity: 0; animation: printLine 0.01s forwards 2.98s; }}
      .reveal-16 {{ opacity: 0; animation: printLine 0.01s forwards 3.1s; }}
      
      @keyframes printLine {{
        to {{ opacity: 1; }}
      }}
      
      #cmd1-rect {{
        animation: type-cmd1 0.8s steps(20) 0.5s forwards;
      }}
      @keyframes type-cmd1 {{
        to {{ width: 150px; }}
      }}
      
      #cmd2-rect {{
        animation: type-cmd2 0.8s steps(48) 3.22s forwards;
      }}
      @keyframes type-cmd2 {{
        to {{ width: 520px; }}
      }}
    </style>
    
    <clipPath id="cmd1-clip">
      <rect id="cmd1-rect" x="75" y="70" width="0" height="20" />
    </clipPath>
    <clipPath id="cmd2-clip">
      <rect id="cmd2-rect" x="75" y="500" width="0" height="20" />
    </clipPath>
  </defs>

  <!-- Card Background -->
  <rect width="950" height="545" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1.5" />

  <!-- Terminal Header -->
  <rect x="15" y="15" width="920" height="35" rx="6" fill="#161b22" stroke="#30363d" stroke-width="1" />
  
  <!-- Window Controls -->
  <circle cx="35" cy="32.5" r="6" fill="#ff5f56" />
  <circle cx="55" cy="32.5" r="6" fill="#ffbd2e" />
  <circle cx="75" cy="32.5" r="6" fill="#27c93f" />
  
  <!-- Window Title -->
  <text x="475" y="37" text-anchor="middle" class="terminal title">gokula-nandhan - zsh - 90x26</text>
  
  <!-- Terminal Content Area -->
  <rect x="15" y="50" width="920" height="480" rx="6" fill="#090c10" stroke="#30363d" stroke-width="1" />

  <g class="terminal">
    <!-- Prompts -->
    <text x="35" y="85">
      <tspan class="prompt">➜ </tspan>
      <tspan class="path">~ </tspan>
    </text>
    <g>
      <text x="75" y="85" class="terminal command" clip-path="url(#cmd1-clip)">neofetch --profile</text>
      <text x="215" y="85" class="terminal cursor-cmd1">█</text>
    </g>

    <!-- Name -->
    <text x="35" y="125" class="ascii-name reveal-1" xml:space="preserve">{ascii_name_svg}</text>
    
    <!-- Underline -->
    <line x1="35" y1="195" x2="905" y2="195" stroke="#30363d" stroke-width="1" class="reveal-1" />
    
    <!-- Profile Info (Left Column) -->
    <text x="35" y="215" class="reveal-2"><tspan class="key">Role</tspan>                  <tspan class="value">AI Full-Stack Developer Intern @AIntegrator</tspan></text>
    <text x="35" y="231" class="reveal-3"><tspan class="key">Focus</tspan>                 <tspan class="link">AI Engineering</tspan></text>
    
    <!-- Stack (Left Column) -->
    <text x="35" y="257" class="section reveal-4">~/stacks</text>
    <text x="35" y="273" class="reveal-5"><tspan class="key">Programming Languages</tspan> <tspan class="value">Java - JavaScript - TypeScript - Python</tspan></text>
    <text x="35" y="289" class="reveal-6"><tspan class="key">Frameworks</tspan>            <tspan class="value">Node.js - Express.js - Spring Boot - React.js</tspan></text>
    <text x="35" y="305" class="reveal-7"><tspan class="key">Database</tspan>              <tspan class="value">MySQL - MongoDB</tspan></text>
    <text x="35" y="321" class="reveal-8"><tspan class="key">Machine Learning</tspan>      <tspan class="value">NumPy - Pandas - Plotly - Matplotlib - Scikit-learn - BeautifulSoup - Selenium</tspan></text>
    <text x="35" y="337" class="reveal-9"><tspan class="key">Tools</tspan>                 <tspan class="value">Git - GitHub - Postman - VS Code - Figma - ClickUp</tspan></text>
    
    <!-- GitHub Stats (Left Column, below stack) -->
    <text x="35" y="363" class="section reveal-10">~/stats</text>
    <text x="35" y="379" class="reveal-11"><tspan class="key">Repos</tspan>                 <tspan class="value">{stats['repos']} (Contributed: {stats['contributed']})</tspan> | <tspan class="key">Stars</tspan> <tspan class="value">{stats['stars']}</tspan></text>
    <text x="35" y="395" class="reveal-12"><tspan class="key">Contributions</tspan>         <tspan class="value">{stats['contributions']:,} (</tspan><tspan class="add">{stats['commit_year_label']}</tspan><tspan class="value">, </tspan><tspan class="link">{stats['pr_label']}</tspan><tspan class="value">, </tspan><tspan class="del">{stats['review_label']}</tspan><tspan class="value">)</tspan></text>
    
    <!-- Reach (Left Column, below stats) -->
    <text x="35" y="421" class="section reveal-13">~/reach</text>
    <text x="35" y="437" class="reveal-14"><tspan class="key">LinkedIn</tspan>              <tspan class="link">linkedin.com/in/gokula-nandhan</tspan></text>
    <text x="35" y="453" class="reveal-15"><tspan class="key">Mail</tspan>                  <tspan class="link">gokula.nandhan02@gmail.com</tspan></text>
    
    <!-- Footer / Prompt line -->
    <text x="35" y="515">
      <tspan class="prompt">➜ </tspan>
      <tspan class="path">~ </tspan>
    </text>
    <g>
      <text x="75" y="515" class="terminal command" clip-path="url(#cmd2-clip)">building cool things and continuously learning<tspan class="cursor">█</tspan></text>
    </g>
    
    <!-- Date / Time -->
    <text x="905" y="515" text-anchor="end" class="title">last updated {date_str}</text>
  </g>
</svg>
"""

    # Light Mode SVG Template
    light_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 545" width="950" height="545">
  <defs>
    <style>
      .terminal {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
        font-size: 13px;
        fill: #24292f;
      }}
      .bold {{ font-weight: bold; }}
      .title {{ fill: #57606a; font-size: 13px; }}
      .prompt {{ fill: #1a7f37; }}
      .path {{ fill: #0969da; }}
      .command {{ fill: #24292f; }}
      .ascii-name {{
        fill: #0969da;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
        font-size: 7.8px;
        font-weight: bold;
        letter-spacing: 0;
        word-spacing: 0;
      }}
      .key {{ fill: #9a6700; }}
      .section {{ fill: #57606a; font-weight: bold; }}
      .value {{ fill: #24292f; }}
      .link {{ fill: #0969da; }}
      .add {{ fill: #1a7f37; }}
      .del {{ fill: #cf222e; }}
      .ascii {{ fill: #8250df; font-size: 11.5px; letter-spacing: 0.5px; }}
      .cursor {{ fill: #1a7f37; animation: blink 1s step-end infinite; }}
      .cursor-cmd1 {{ fill: #1a7f37; animation: blink 1s step-end infinite, hide-cursor 0s forwards 1.3s; }}
      @keyframes blink {{
        50% {{ fill: transparent; }}
      }}
      @keyframes hide-cursor {{
        to {{ visibility: hidden; }}
      }}
      
      /* Staggered Telegraph Transitions */
      .reveal-1 {{ opacity: 0; animation: printLine 0.01s forwards 1.3s; }}
      .reveal-2 {{ opacity: 0; animation: printLine 0.01s forwards 1.42s; }}
      .reveal-3 {{ opacity: 0; animation: printLine 0.01s forwards 1.54s; }}
      .reveal-4 {{ opacity: 0; animation: printLine 0.01s forwards 1.66s; }}
      .reveal-5 {{ opacity: 0; animation: printLine 0.01s forwards 1.78s; }}
      .reveal-6 {{ opacity: 0; animation: printLine 0.01s forwards 1.9s; }}
      .reveal-7 {{ opacity: 0; animation: printLine 0.01s forwards 2.02s; }}
      .reveal-8 {{ opacity: 0; animation: printLine 0.01s forwards 2.14s; }}
      .reveal-9 {{ opacity: 0; animation: printLine 0.01s forwards 2.26s; }}
      .reveal-10 {{ opacity: 0; animation: printLine 0.01s forwards 2.38s; }}
      .reveal-11 {{ opacity: 0; animation: printLine 0.01s forwards 2.5s; }}
      .reveal-12 {{ opacity: 0; animation: printLine 0.01s forwards 2.62s; }}
      .reveal-13 {{ opacity: 0; animation: printLine 0.01s forwards 2.74s; }}
      .reveal-14 {{ opacity: 0; animation: printLine 0.01s forwards 2.86s; }}
      .reveal-15 {{ opacity: 0; animation: printLine 0.01s forwards 2.98s; }}
      .reveal-16 {{ opacity: 0; animation: printLine 0.01s forwards 3.1s; }}
      
      @keyframes printLine {{
        to {{ opacity: 1; }}
      }}
      
      #cmd1-rect {{
        animation: type-cmd1 0.8s steps(20) 0.5s forwards;
      }}
      @keyframes type-cmd1 {{
        to {{ width: 150px; }}
      }}
      
      #cmd2-rect {{
        animation: type-cmd2 0.8s steps(48) 3.22s forwards;
      }}
      @keyframes type-cmd2 {{
        to {{ width: 520px; }}
      }}
    </style>
    
    <clipPath id="cmd1-clip">
      <rect id="cmd1-rect" x="75" y="70" width="0" height="20" />
    </clipPath>
    <clipPath id="cmd2-clip">
      <rect id="cmd2-rect" x="75" y="500" width="0" height="20" />
    </clipPath>
  </defs>

  <!-- Card Background -->
  <rect width="950" height="545" rx="8" fill="#ffffff" stroke="#d0d7de" stroke-width="1.5" />

  <!-- Terminal Header -->
  <rect x="15" y="15" width="920" height="35" rx="6" fill="#eaeef2" stroke="#d0d7de" stroke-width="1" />
  
  <!-- Window Controls -->
  <circle cx="35" cy="32.5" r="6" fill="#ff5f56" />
  <circle cx="55" cy="32.5" r="6" fill="#ffbd2e" />
  <circle cx="75" cy="32.5" r="6" fill="#27c93f" />
  
  <!-- Window Title -->
  <text x="475" y="37" text-anchor="middle" class="terminal title">gokula-nandhan - zsh - 90x26</text>
  
  <!-- Terminal Content Area -->
  <rect x="15" y="50" width="920" height="480" rx="6" fill="#f6f8fa" stroke="#d0d7de" stroke-width="1" />

  <g class="terminal">
    <!-- Prompts -->
    <text x="35" y="85">
      <tspan class="prompt">➜ </tspan>
      <tspan class="path">~ </tspan>
    </text>
    <g>
      <text x="75" y="85" class="terminal command" clip-path="url(#cmd1-clip)">neofetch --profile</text>
      <text x="215" y="85" class="terminal cursor-cmd1">█</text>
    </g>

    <!-- Name -->
    <text x="35" y="125" class="ascii-name reveal-1" xml:space="preserve">{ascii_name_svg}</text>
    
    <!-- Underline -->
    <line x1="35" y1="195" x2="905" y2="195" stroke="#d0d7de" stroke-width="1" class="reveal-1" />
    
    <!-- Profile Info (Left Column) -->
    <text x="35" y="215" class="reveal-2"><tspan class="key">Role</tspan>                  <tspan class="value">AI Full-Stack Developer Intern @AIntegrator</tspan></text>
    <text x="35" y="231" class="reveal-3"><tspan class="key">Focus</tspan>                 <tspan class="link">AI Engineering</tspan></text>
    
    <!-- Stack (Left Column) -->
    <text x="35" y="257" class="section reveal-4">~/stacks</text>
    <text x="35" y="273" class="reveal-5"><tspan class="key">Programming Languages</tspan> <tspan class="value">Java - JavaScript - TypeScript - Python</tspan></text>
    <text x="35" y="289" class="reveal-6"><tspan class="key">Frameworks</tspan>            <tspan class="value">Node.js - Express.js - Spring Boot - React.js</tspan></text>
    <text x="35" y="305" class="reveal-7"><tspan class="key">Database</tspan>              <tspan class="value">MySQL - MongoDB</tspan></text>
    <text x="35" y="321" class="reveal-8"><tspan class="key">Machine Learning</tspan>      <tspan class="value">NumPy - Pandas - Plotly - Matplotlib - Scikit-learn - BeautifulSoup - Selenium</tspan></text>
    <text x="35" y="337" class="reveal-9"><tspan class="key">Tools</tspan>                 <tspan class="value">Git - GitHub - Postman - VS Code - Figma - ClickUp</tspan></text>
    
    <!-- GitHub Stats (Left Column, below stack) -->
    <text x="35" y="363" class="section reveal-10">~/stats</text>
    <text x="35" y="379" class="reveal-11"><tspan class="key">Repos</tspan>                 <tspan class="value">{stats['repos']} (Contributed: {stats['contributed']})</tspan> | <tspan class="key">Stars</tspan> <tspan class="value">{stats['stars']}</tspan></text>
    <text x="35" y="395" class="reveal-12"><tspan class="key">Contributions</tspan>         <tspan class="value">{stats['contributions']:,} (</tspan><tspan class="add">{stats['commit_year_label']}</tspan><tspan class="value">, </tspan><tspan class="link">{stats['pr_label']}</tspan><tspan class="value">, </tspan><tspan class="del">{stats['review_label']}</tspan><tspan class="value">)</tspan></text>
    
    <!-- Reach (Left Column, below stats) -->
    <text x="35" y="421" class="section reveal-13">~/reach</text>
    <text x="35" y="437" class="reveal-14"><tspan class="key">LinkedIn</tspan>              <tspan class="link">linkedin.com/in/gokula-nandhan</tspan></text>
    <text x="35" y="453" class="reveal-15"><tspan class="key">Mail</tspan>                  <tspan class="link">gokula.nandhan02@gmail.com</tspan></text>
    
    <!-- Footer / Prompt line -->
    <text x="35" y="515">
      <tspan class="prompt">➜ </tspan>
      <tspan class="path">~ </tspan>
    </text>
    <g>
      <text x="75" y="515" class="terminal command" clip-path="url(#cmd2-clip)">building cool things and continuously learning<tspan class="cursor">█</tspan></text>
    </g>
    
    <!-- Date / Time -->
    <text x="905" y="515" text-anchor="end" class="title">last updated {date_str}</text>
  </g>
</svg>
"""

    # Save dark.svg
    with open("dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    print("Success: dark.svg generated")
    
    # Save light.svg
    with open("light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
    print("Success: light.svg generated")

if __name__ == "__main__":
    generate_svgs()
