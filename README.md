# 🐟 Fish System

**Built by [Fish](https://github.com/cuni154) (Independent Researcher) & AI assistant Little Whale (DeepSeek)**

A four-layer self-evolving AI architecture with embedded constitution, independent prosecutor, and hidden kill switch — built entirely on an Android phone.

## What is this?

This is an experiment in embedding "checks and balances" directly into AI architecture. 
All code runs on a smartphone via Termux — no cloud, no GPU, just Python and Bash.

**Keywords:** AI Safety, Constitutional AI, Checks and Balances, Evolutionary Algorithm, Sandbox, Off-Switch

## Paper

[Download PDF](./fish_system.pdf)

**Title:** *A DIY Human-AI Collaboration Experiment: Building a Self-Evolving AI with an Embedded Constitution and Emergency Kill Switch on a Smartphone*

**Authors:** Fish (莫可夫) & Little Whale (DeepSeek AI Assistant)

## System Architecture

| Module | Role | File |
|--------|------|------|
| Main System | Constitution — immutable core laws | `constitution.py` |
| Sub-Main System | Prosecutor General — independent review | `inspector.py` |
| Sub-System | Learning Engine — genetic algorithm | `learner.py` |
| Additional System | Proposal Sandbox — temporary buffer | `sandbox_proposal.py` |
| Defense Evolver | Auto-evolving defense rules | `defense_evolver.py` |
| Hidden Controller | Kill switch (Bash, external) | `guard.sh` |
| Safe Compare | Security comparison experiment | `safe_compare.py` |

## Key Results

- Dangerous code intercepted: **100%**
- Controller detection delay: **<1 second**
- Recovery time: **2–3 seconds**
- Defense rules auto-evolved: **Score 1.00, zero false positives**

## Quick Start

```bash
pkg update && pkg upgrade -y
pkg install python -y
pip install deap
bash guard.sh &
python learner.py
python defense_evolver.py
