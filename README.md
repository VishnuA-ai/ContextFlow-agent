# ✨ ContextFlow

## Multi-Agent AI Consensus Engine

> *Preventing AI hallucinations before they happen*

[![AWS Strands](https://img.shields.io/badge/AWS-Strands%20Agents-FF9900?logo=amazon-aws)](https://aws.amazon.com)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)](https://github.com/VishnuA-ai/ContextFlow-agent)
[![React](https://img.shields.io/badge/React-18.3-61dafb)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Working-009688)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)

---

## 🎯 The Problem

When multiple AI agents work together, they often have **different information** about the same thing.

### Real-World Examples

**Legal:** 
- Scout Agent extracts deadline: **March 15**
- Critic Agent extracts deadline: **March 25**
- ❌ Without ContextFlow: One date silently propagates (WRONG CONTRACT DATE)
- ✅ With ContextFlow: FLAGGED FOR HUMAN REVIEW

**Healthcare:**
- Doctor AI #1: "Patient needs surgery"
- Doctor AI #2: "Patient needs medication"
- ❌ Without ContextFlow: Conflicting treatment recommendations
- ✅ With ContextFlow: DETECTED AND FLAGGED

**Finance:**
- Trading Bot #1: "BUY"
- Trading Bot #2: "SELL"
- ❌ Without ContextFlow: Contradictory trades execute
- ✅ With ContextFlow: CONFLICT PREVENTED

**Research:**
- Scout Agent: "Paper has **145** citations"
- Critic Agent: "Paper has **156** citations"
- ❌ Without ContextFlow: Wrong number published (HALLUCINATION)
- ✅ With ContextFlow: **Resolved to 150** (consensus)

This is **context drift** — when agents develop different understandings of the same information. It causes hallucinations that *sound confident but are completely wrong.*

---

## 💡 The Solution

ContextFlow is a **consensus layer** that:

1. **Detects** agent divergence in real-time (<50ms)
2. **Prevents** hallucinations before they propagate
3. **Flags** unresolvable conflicts for human review
4. **Audits** every decision (immutable journal)

### How It Works
