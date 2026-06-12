# Complete Research Report: Claude Fable 5, Mythos 5, and Project Glasswing

> **Research Date**: June 12, 2026
> **Methodology**: Multi-source deep research with adversarial verification (71 claims extracted, 25 verified, 20 confirmed, 5 refuted)
> **Sources**: 17 fetched across 5 research angles (Anthropic official docs, Cloudflare blog, TechCrunch, CyberScoop, Harvard CorpGov, CSA, The Hacker News)

---

## Executive Summary

Claude Fable 5 and Claude Mythos 5 were **announced June 9, 2026** as Anthropic's next-generation frontier models. Fable 5 is the generally available flagship; Mythos 5 is the **same underlying model with cybersecurity safeguards removed**, deployed exclusively through **Project Glasswing** — a collaborative initiative launched April 7, 2026, now expanded to ~200 organizations across 15+ countries, that has already discovered **over 10,000 high/critical-severity vulnerabilities** in systemically important software.

---

## 1. Claude Fable 5 — Full Technical Profile

### Specifications

| Specification | Value | Source |
|---|---|---|
| Model ID | `claude-fable-5` | Anthropic docs |
| Release Date | June 9, 2026 | Anthropic announcement |
| Context Window | 1,000,000 tokens | Confirmed |
| Max Output | 128,000 tokens | Confirmed |
| Input Pricing | $10.00 / 1M tokens | Confirmed |
| Output Pricing | $50.00 / 1M tokens | Confirmed |
| Thinking | Always on (cannot be disabled) | API docs |
| Data Retention | 30-day minimum required | API docs |
| Tokenizer | New (~30% more tokens vs Opus-tier) | API docs |

### Key Technical Differentiators from Prior Models

#### Always-On Protected Thinking

- `thinking: {type: "disabled"}` returns a 400 error (accepted on Opus 4.7/4.8)
- `thinking: {type: "enabled", budget_tokens: N}` also returns a 400
- Raw chain of thought is **never exposed** — only summaries via `display: "summarized"`
- Depth controlled via `output_config.effort` (`low`/`medium`/`high`/`xhigh`/`max`)

#### Safety Classifiers with Automatic Fallback

- Classifiers target: **cybersecurity**, **biology/chemistry**, and **distillation** queries
- Declined requests automatically fall back to Claude Opus 4.8 (via server-side `fallbacks` parameter)
- Returns `stop_reason: "refusal"` with `stop_details.category` (`"cyber"`, `"bio"`, `"reasoning_extraction"`)
- External bug bounty: **zero harmful single-turn request compliance in 1,000+ hours of testing**

#### Other Breaking Changes

- **No Sampling Parameters** — `temperature`, `top_p`, `top_k` all removed
- **No Assistant Prefill** — Last-assistant-turn prefills return 400
- **New Tokenizer** — ~30% more tokens for the same content vs Opus-tier

### Capabilities

- **15+ minute autonomous sessions** on hard tasks
- **Parallel sub-agent delegation** with sustained multi-agent communication
- **Self-verification** against specifications
- **Repository-history search** and one-shot debugging
- **Enterprise deliverables** — financial analysis, spreadsheets, slides, docs
- **High-resolution vision** (no downscaling cap)
- **Memory** — Performs notably better when given a memory surface

### Effort Levels

| Level | Recommended Use |
|---|---|
| `low` | Routine work — still exceeds prior models' `xhigh`/`max` performance |
| `medium` | Cost-sensitive use cases balancing quality and token usage |
| `high` | **Default for most tasks** |
| `xhigh` | Most capability-sensitive workloads (coding/agentic) |
| `max` | Hardest, latency-insensitive cases |

---

## 2. Claude Mythos 5 — The Glasswing Model

### Verified Relationship to Fable 5

> *"It's the same underlying model as Fable 5, but with the safeguards lifted in some areas"*
> — Anthropic announcement, June 9, 2026

| Aspect | Claude Fable 5 | Claude Mythos 5 |
|---|---|---|
| Model ID | `claude-fable-5` | `claude-mythos-5` |
| Availability | **General release** | **Project Glasswing only** (invitation-only, no self-serve) |
| US Government | No special relationship | **Deployed in collaboration with the US government** |
| Cybersecurity classifiers | **Active** (blocks most cyber content) | **Lifted** |
| Pricing | $10/$50 per MTok | $10/$50 per MTok |
| All other capabilities | Identical | Identical |

### Lineage

```
Claude Mythos Preview (invitation-only, April 2026)
        |
        v
Claude Mythos 5 (claude-mythos-5, June 9, 2026 — still Glasswing-only)
```

### Benchmark Performance

| Benchmark | Claude Mythos Preview | Claude Opus 4.6 |
|---|---|---|
| **CyberGym** (vulnerability reproduction) | **83.1%** | 66.6% |

> *Note: CyberGym benchmark lacks clear independent provenance (cybergym.ai is a parked domain).*

---

## 3. Project Glasswing — Program Details

### Overview

Project Glasswing is Anthropic's **collaborative initiative to find vulnerabilities in critical software before AI can be weaponized against it**. It provides authorized partners access to Claude Mythos (now Mythos 5) with cybersecurity safeguards removed.

### Timeline

| Date | Milestone |
|---|---|
| **April 7, 2026** | Project Glasswing launches with 12 partners |
| **May 18, 2026** | Cloudflare publishes independent findings from 50+ repositories |
| **May 22, 2026** | Glasswing initial research update: 10,000+ vulnerabilities reported |
| **June 2, 2026** | Expansion to ~150 additional organizations across 15+ countries |
| **June 9, 2026** | Claude Mythos 5 announced (successor to Mythos Preview) |

### Launch Partners (Verified)

- **AWS**
- **Apple**
- **Microsoft**
- **Google**
- **CrowdStrike**
- **Palo Alto Networks**
- Plus 6 additional unnamed partners
- **40+ organizations maintaining critical infrastructure**

### Expansion (June 2, 2026)

- ~150 additional organizations
- 15+ countries
- Focus: **power, water, healthcare, and communications sectors**
- Target: infrastructure where attacks could affect **over 100 million people**

### Access Model

- **Invitation-only** — no self-serve sign-up
- Deployed **in collaboration with the US government**
- Participants are vetted organizations

---

## 4. Cybersecurity Results & Proven Use Cases

### Verified Results (Adversarially Confirmed)

| Metric | Value | Verification |
|---|---|---|
| Total vulnerabilities found by partners | **10,000+** high/critical-severity | 3-0 consensus |
| Open-source projects scanned by Anthropic | **1,000+** | 3-0 consensus |
| Estimated vulnerabilities in those projects | **6,202** | 3-0 consensus |
| True positive rate (assessed subset) | **90.6%** (1,587 of 1,752 assessed) | 3-0 consensus |
| Independent validation | **6 security firms** validated open-source results | 3-0 consensus |
| Cloudflare results | **2,000 bugs, 400 high/critical** across 50+ repos | 3-0 consensus |

### Landmark Discoveries

1. **27-year-old vulnerability in OpenBSD** — Allows remote crashes (found autonomously)
2. **16-year-old vulnerability in FFmpeg** — Eluded five million automated tests (found autonomously)

> *Note: No CVE identifiers publicly provided; independent confirmation from maintainers not found. Medium confidence.*

### Autonomous Operation Model (Verified by Cloudflare)

Mythos Preview operates **without human steering**:

1. Identifies potential vulnerability patterns in source code
2. **Writes exploit code** from scratch
3. **Compiles it** in scratch environments
4. **Runs it** against the target
5. **Reads failure output** and adjusts hypotheses
6. **Iterates** until the vulnerability is confirmed or disproven

> *Source: Cloudflare blog (May 18, 2026) — first-hand confirmation from testing 50+ repositories.*

### Verified Use Cases (from Anthropic & Partners)

| Use Case | Description | Source |
|---|---|---|
| **Pre-release vulnerability prevention** | Scanning software before deployment to find vulnerabilities before attackers do | Anthropic expansion announcement |
| **Penetration testing** | Autonomous security testing of infrastructure and applications | Anthropic + Cloudflare blog |
| **Threat detection & response automation** | Automated analysis and response to security threats in real-time | Anthropic expansion announcement |
| **Legacy codebase migration to memory-safe languages** | Rebuilding vulnerable C/C++ codebases in Rust or other safe languages | Anthropic expansion announcement |
| **Open-source scanning at scale** | Automated vulnerability discovery across 1,000+ projects | Anthropic research update |

---

## 5. Cybersecurity Use Cases Enabled by Technical Capabilities

### A. Vulnerability Discovery & Assessment

| Capability Used | Cybersecurity Application |
|---|---|
| Long-horizon autonomous execution (15+ min) | Deep code auditing that requires following complex execution paths |
| Exploit writing + compilation + testing loop | Proof-of-concept generation to validate vulnerabilities |
| 1M context window | Ingesting entire codebases for holistic security analysis |
| Self-verification against rubrics | Confirming true positives vs false positives (90.6% rate) |
| Repository-history search | Finding when security regressions were introduced |

### B. Incident Response & Forensics

| Capability Used | Cybersecurity Application |
|---|---|
| 1M context window | Ingesting and correlating massive log datasets |
| Long-horizon reasoning | Root cause analysis across complex system interactions |
| Parallel sub-agent delegation | Simultaneous analysis of multiple forensic artifacts |
| Always-on thinking | Deep reasoning about attack chains and lateral movement |

### C. Automated Penetration Testing

| Capability Used | Cybersecurity Application |
|---|---|
| Tool use (bash, code execution) | Operating security toolchains autonomously |
| Autonomous iteration | Writing, testing, and refining exploits without human input |
| Memory across sessions | Building institutional knowledge of target environments |
| Self-verification | Confirming exploitation success before reporting |

### D. Security Operations & Automation

| Capability Used | Cybersecurity Application |
|---|---|
| Managed Agents (persistent) | SOAR-like automated security orchestration |
| Scheduled deployments | Nightly/weekly automated security scans |
| Outcome-based grading | Measuring scan completeness against rubrics |
| MCP integration | Connecting to SIEM, ticketing, CI/CD tools |

### E. Critical Infrastructure Defense

| Capability Used | Cybersecurity Application |
|---|---|
| Scale (1000+ project scanning) | Systematic vulnerability discovery across entire sectors |
| 90.6% true positive rate | Actionable findings without drowning in false positives |
| Autonomous operation | Reducing human analyst burden for repetitive scanning |
| Legacy code analysis | Assessing SCADA/ICS systems written in unsafe languages |

### F. Managed Agents Architecture for Security Operations

```
Agent: "Security Scanner"
+-- Tools: agent_toolset_20260401 (bash, file ops, web search)
+-- MCP Servers: GitHub, Jira/Linear (for ticket creation)
+-- Custom Tools: SIEM integration, scanner APIs
+-- Skills: vulnerability assessment, compliance checking
+-- Schedule: Nightly compliance scan (via Deployments)
```

---

## 6. Safeguards & Oversight

- Anthropic deploys **cyber safeguards** on generally available models to detect malware development and data exfiltration
- Anthropic is in **discussions with MITRE** about evolving the ATT&CK framework to include AI-enabled threat behaviors
- Bug bounty found **zero universal jailbreaks** in 1,000+ hours of testing on Fable 5
- Glasswing access is controlled through vetting and US government collaboration

---

## 7. Refuted Claims

The following claims were extracted from sources but **refuted** during adversarial verification:

| Claim | Vote | Reason |
|---|---|---|
| Mozilla found 271 vulnerabilities in Firefox 150 with Mythos Preview | 0-3 | Not independently verifiable |
| Mythos Preview is available at $25/$125 per MTok on Bedrock/Vertex/Foundry | 1-2 | Contradicts verified access model (Glasswing-only) |
| Mythos can chain attack primitives into full exploitation (use-after-free to arbitrary RW + ROP) | 0-3 | Overly specific technical claim not supported by sources |
| Mythos produces "noticeably higher quality" output than all prior models | 1-2 | Subjective/promotional characterization |
| Anthropic describes Mythos 5 as "strongest cybersecurity capabilities of any model in the world" | 0-3 | Exact quote not found in cited source |

---

## 8. Open Questions

1. **What CVEs have been assigned** to Glasswing-discovered vulnerabilities? No public CVE identifiers provided.
2. **What technical differences exist** between Mythos 5 and Fable 5 beyond safeguard removal? Is there cybersecurity-specific fine-tuning?
3. **What oversight mechanisms** govern partner use of Mythos 5's unrestricted capabilities?
4. **What is the US government's specific role** — which agencies, what access, what vetting process?

---

## 9. Key Sources

| Source | Type | URL |
|---|---|---|
| Anthropic: Fable 5 / Mythos 5 Announcement | Primary | https://www.anthropic.com/news/claude-fable-5-mythos-5 |
| Anthropic: Project Glasswing | Primary | https://www.anthropic.com/glasswing |
| Anthropic: Expanding Project Glasswing | Primary | https://www.anthropic.com/news/expanding-project-glasswing |
| Anthropic: Glasswing Initial Update | Primary | https://www.anthropic.com/research/glasswing-initial-update |
| Cloudflare: Cyber Frontier Models | Primary (Partner) | https://blog.cloudflare.com/cyber-frontier-models/ |
| Anthropic: AI-Enabled Cyber Threats & MITRE | Primary | https://www.anthropic.com/news/AI-enabled-cyber-threats-mitre-attack |
| Anthropic: Platform Documentation | Primary | https://platform.claude.com/docs/en/docs/about-claude/models |
| TechCrunch: Glasswing Expansion | Secondary | https://techcrunch.com/2026/06/02/anthropic-scales-claude-mythos-to-critical-infrastructure-in-15-countries/ |
| CyberScoop: Glasswing Expansion | Secondary | https://cyberscoop.com/anthropic-project-glasswing-expansion-critical-infrastructure-claude-mythos/ |
| Harvard CorpGov: Corporate Board Guidance | Secondary | https://corpgov.law.harvard.edu/2026/05/24/what-corporate-boards-need-to-know-and-do-about-anthropics-mythos-and-project-glasswing/ |

---

## 10. Caveats

- Nearly all sources are first-party Anthropic announcements or partner blogs, which are authoritative for describing their own products but inherently promotional.
- The 10,000+ vulnerability count is self-reported with only partial independent validation (six security firms assessed a subset).
- No CVE identifiers are provided for headline discoveries (OpenBSD, FFmpeg).
- The 90.6% true positive rate applies only to 1,752 assessed findings out of 6,202 total — the majority remain unvalidated.
- Claims about Mythos Preview operating "entirely autonomously" are qualified in the source as "nearly all" findings being autonomous.
- The 100-million-people-affected figure for critical infrastructure is Anthropic's own estimate without external validation.
- These findings reflect information as of June 12, 2026, and the program is actively expanding.

---

## Summary Table

| Model | Purpose | Access | Cyber Classifiers |
|---|---|---|---|
| **Claude Fable 5** | General frontier AI | Public API | **Active** — blocks most cybersecurity content |
| **Claude Mythos 5** | Authorized cybersecurity work | **Project Glasswing only** | **Lifted** |
| **Project Glasswing** | Defensive cybersecurity at scale | ~200 orgs, 15+ countries, US govt collaboration | N/A — program provides the access |
