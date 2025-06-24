# SWE-Agent

A reference implementation of a **Software Engineering Agent** that connects to a remote VM to fetch, analyze, and plan automated repairs of repository issues. <br>
remaining components (Planer, Executor ...) are pending.

---

## Goal

Build an agent that:

1. **Connects to a VM** (via gbox) to execute commands, read/write files, and install dependencies in a controlled sandbox.  
2. **Fetches issues** from a GitHub repository.  
3. **Transforms** each issue into a `StructuredIssue` object (intent, crash flag, code locations, repro steps, summary).  
4. **Decomposes** that structure into ordered subtasks (locate, patch, test, PR).  
5. **(Future)** Executes tasks on the VM, validates fixes, and opens pull requests.

---
## Directory Layout

```text
SWE_agent/
├── intake/                # Module 1: Issue Intake
│   ├── fetcher.py         # fetch_issues(): pull raw issues via GitHub API
│   ├── cleaner.py         # clean_text(): strip fences, collapse blank lines
│   ├── classifier.py      # classify_intent(), detect_crash(): LLM classification
│   ├── extractor.py       # extract_entities(): LLM-based extraction
│   ├── summarizer.py      # summarize_issue(): LLM-based one-sentence summary
│   ├── schema.py          # RawIssue, Entity, StructuredIssue data classes
│   └── pipeline.py        # LangGraph pipeline and run_intake()
│
├── planner/               # Module 2: Task Planner
│   ├── pending    
│   ├── pending
│   └── pipeline.py        # LangGraph pipeline and run_planner()
│
├── executor/              
│   └── …
├── pending/               
│   └── …
├── pending/                    
│   └── …
├── main.py                # Entry point: orchestrates all modules
└── requirements.txt       # Python dependencies
