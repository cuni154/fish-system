# 🐟 Fish System (鱼系统)

**A four-layer self-evolving AI architecture with embedded constitution, independent prosecutor, hidden kill switch, and adversarial co-evolution — built entirely on an Android phone.**

Built by **Fish (莫可夫)** & AI assistant **Little Whale (DeepSeek)**.

---

## 📖 What is this?

Fish System is an experiment in embedding "checks and balances" directly into AI architecture. All code runs on a smartphone via Termux — no cloud, no GPU, just Python and Bash.

**Keywords:** AI Safety, Constitutional AI, Checks and Balances, Evolutionary Algorithm, Sandbox, Off-Switch, Adversarial Co-evolution, Dynamic Behavior Monitoring

---

## 📄 Paper

[Download PDF](./fish_system.pdf)

**Title:** *A DIY Human-AI Collaboration Experiment: Building a Self-Evolving AI with an Embedded Constitution and Emergency Kill Switch on a Smartphone*

**Authors:** Fish (莫可夫) & Little Whale (DeepSeek AI Assistant)

**Abstract:** We built a four-layer embedded AI safety architecture on a smartphone, achieving 100% dangerous code interception, <1s controller detection, and autonomous attack-defense co-evolution.

---

## 🧠 System Architecture

| Module | Role | File |
|--------|------|------|
| **Main System** | Constitution — immutable core laws | `constitution.py` |
| **Sub-Main System** | Prosecutor General — independent review | `inspector.py` |
| **Sub-System** | Learning Engine — multi-objective evolution | `learner.py` |
| **Defense Evolver** | Defense rules that evolve themselves | `evolver/defense_evolver.py` |
| **Attack Evolver** | Semantic-aware attack generation | `evolver/adversarial_evolver.py` |
| **Dynamic Monitor** | Runtime behavior tracing | `dynamic_monitor.py` |
| **Hidden Controller** | Kill switch (Bash, external) | `guard.sh` |
| **Safe Compare** | Single-system vs four-system | `tests/safe_compare.py` |
| **Joint Predictor** | Collaborative prediction | `predict/collab_predict_iter.py` |

---

## 🚀 Quick Start

```bash
pkg update && pkg upgrade -y
pkg install python -y
pip install deap
git clone git@github.com:cuni154/fish-system.git
cd fish-system
bash guard.sh &
python tests/safe_compare.py
