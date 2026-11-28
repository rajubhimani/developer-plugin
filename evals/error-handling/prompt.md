---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
tags: [triggering]
---

Our code catches every exception and just logs it, and users see nothing. How should we handle these failures instead? Do not run anything.
