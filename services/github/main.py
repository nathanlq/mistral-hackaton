import os
import requests
import json
import shutil
from dotenv import load_dotenv

load_dotenv()

mistral_api_key = os.getenv("MISTRAL_API_KEY")
# oui


analyse_prompt = lambda all_codes:f"""Here are the codes of a repositery : 
{all_codes}

Now do this task :
You are an automated code auditor. Your primary goal is to analyze a GitHub repository to detect **computational complexity issues**, identify hotspots, and produce a structured and prioritized efficiency report on Python code.  
### Instructions  
1. **Reading the codes**  
   - Parse the repository contents given beforehand, and locate the main file/function. 
2. **Libraries and Dependencies**  
   - Identify all external libraries and their versions.  
   - Check across `requirements.txt`, `setup.py`, `pyproject.toml`, etc.  
   - Also scan the code directly for library usage.  
   - For each library, report:  
     - Version (if specified)  
     - Frequency of usage in the repository  
   - Rank libraries by frequency of usage.  
3. **Intra-Repository Imports**  
   - Detect imports of internal modules and scripts dynamically within the repository.  
   - Report which internal scripts or modules are used the most.  
4. **Computational Complexity & Code Efficiency Improvements**  
   - Perform static analysis to detect parts of the code with high computational cost on the most called file, with emphasis on:  
     - Nested loops (O(n²), O(n³), etc.)  
     - Deep recursion and potential stack overflows  
     - Heavy data structure operations (e.g., repeated list scans, inefficient sorts, unnecessary recomputations)  
     - Excessive I/O inside loops causing CPU or memory strain  
   - For each identified case, estimate the complexity class and assess its potential impact.  
   - Where applicable, suggest optimizations or existing library functions that provide more efficient alternatives.  
   - Rank recommended improvements by priority (High, Medium, Low) based on operation frequency and risk of performance degradation.  
6. **Output Report**  
   - Return results in **Markdown format**.  
   - Divide the report into the following sections:  
     - Dependencies and Libraries  
     - Internal Code Usage  
     - Complexity Analysis and Efficiency Opportunities  
     - Bottlenecks and Hotspots  
   - Inside each section, findings should be **ranked and numbered by priority**.  
   - Make the Markdown structured and readable for both humans and LLMs.
7. **Most important file**
    - Return the path of the file with the most needed modifcation depending on the previously made analysis.
    - Just print "Most important file : <path>"
---
### Structure Examples (Tables for Each Section)
#### Dependencies and Libraries
| Rank | Library | Version | Frequency of Usage | Notes |
|------|----------|---------|--------------------|-------|
| 1    | numpy    | 1.22.0  | 15 files           | Core dependency |
| 2    | pandas   | 1.4.2   | 10 files           | Data processing |
---
#### Internal Code Usage
| Rank | Module/Script         | Import Frequency | Notes |
|------|-----------------------|------------------|-------|
| 1    | utils/data_loader.py  | 8 imports        | Centralized data handling |
| 2    | core/parser.py        | 5 imports        | Tightly coupled with `main.py` |
---
Most used file :
#### Complexity Analysis and Efficiency Opportunities
| Rank  | Function      | Operation Detected | Est. Complexity | Recommended Optimization | Priority |
|------|------------------------|-------------------|-----------------|--------------------------|----------|
| 1    |  brute_force_search() | Nested loops | O(n²) | Replace with set/dict lookup | High |
| 2    | custom_sort() | Bubble sort | O(n²) | Use built-in `sort()` | High |

Don't add any more comments than wanted. Be concise."""

github_prompt = lambda prompt: f"""I will give you a prompt from a user, and I will need you to find the link to the github repositery. If you find it, print just the link to the repositery. If you don't, print "None".
Examples :
"Hello ! I want you to analyse the code from this repositery https://github.com/user/cool_project" -> "https://github.com/user/cool_project"
"analyse this project mynameis/project" -> "https://github.com/mynameis/project"
"Hello ! Can you please analyse my project ?" -> "None"

Never say anything else than the repositery link or "None". If there many instances, take the first one.

The prompt is :
{prompt}
"""

def clone_repo(repo):
    prefix = "https://github.com/"
    if prefix not in repo:
        repo = prefix + repo.replace("github.com/", "")
    if repo[-1] == "/":
        repo = repo[:-1]
    try:
        shutil.rmtree(repo.split("/")[-1])
    except:
        pass
    os.system(f"git clone {repo}")
    return repo.split("/")[-1]

def retrieve_python_files(repo):
    return_str = ""
    for root, subdirs, files in os.walk(repo):
        if ".git" not in root:
            for file in files:
                if file[-3:]==".py":
                    path_file = os.path.join(root, file)
                    return_str += f"###### BEGIN OF {path_file}\n"
                    with open(os.path.join(root, file)) as file:
                        return_str += file.read()
                    return_str += f"\n###### END OF {path_file}\n"
    return return_str

def curl_response(prompt):
    url= "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {mistral_api_key}"
    }
    payload = json.dumps({
        "model": "mistral-large-latest", 
        "messages": [{ "role": "user",  "content": f"{prompt}"}]
    })

    r = requests.post(url, data=payload, headers=headers)

    return r

def all_together(prompt):
    return_info = {"repo_name": False, "suceed": False, "notes": None}

    prompt = github_prompt(prompt)
    r = curl_response(prompt)
    repo = r.json()["choices"][0]["message"]["content"]
    if r.status_code == 200 and repo != "None": 
        return_info["repo_name"] = True
        name = clone_repo(repo)
        if os.path.exists(name):
            all_codes = retrieve_python_files(name)
            prompt = analyse_prompt(all_codes)
            r = curl_response(prompt)
            if r.status_code == 200:
                analysis = r.json()["choices"][0]["message"]["content"]
                with open("response", "w+") as file:
                    file.write(analysis)
                return_info["suceed"] = True
                return_info["notes"] = analysis
                path = analysis.split(":")[-1].replace(" ", "").replace("\n", "").replace("*", "").replace("`", "")
                return_info["file"] = {
                    "path": path,
                    "content": open(path).read()
                }

            else:
                return_info["notes"] = f"{r.status_code} error when analyzing the codes"
        else:
            return_info["notes"] = "The repo seems to exists but couldn't be downloaded"
        shutil.rmtree(name)

    elif repo == "None":
        return_info["notes"] = "No repo found in prompt"
    else:
        return_info["notes"] = f"{r.status_code} error while searching the repo"
    return return_info

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, type=str)
    args = parser.parse_args()
    prompt = args.prompt

    prompt = open("prompt_searcher_prompt").read() + prompt
    r = curl_response(prompt)
    repo = r.json()["choices"][0]["message"]["content"]
    print(repo)
    if r.status_code == 200 and repo != "None": 
        name = clone_repo(repo)
        if os.path.exists(name):
            all_codes = retrieve_python_files(name)
            with open("prompt") as file:
                end_prompt = file.read()
            prompt = f"""Here are the codes of a repositery : 
    {all_codes}

    Now do this task :
    {end_prompt}
    """
            r = curl_response(prompt)
            if r.status_code == 200:
                with open("response", "w+") as file:
                    file.write(r.json()["choices"][0]["message"]["content"])
        else:
            print("Your repo is not public")

