---
name: design-patterns
description: Design patterns and principles (composition, small interfaces, dependency inversion), and when not to use them. Use when designing a module, adding an abstraction, or reviewing over-engineered or tangled code.
verified: 2026-11-19
---

# Design patterns and principles

A pattern is a named answer to a recurring problem. Start from the problem, never
from the pattern. If you cannot state the problem in one sentence, do not add it.

## Rules

1. **Simplest thing first.** A function and a data type beat a class hierarchy.
   Add structure when a second real case or a real change forces it.
2. **Wait for the third case.** Copy once, tolerate twice, abstract on the third,
   when you can see what actually varies. A wrong abstraction costs more than
   duplication.
3. **Composition over inheritance.** Inherit only for a true "is a" relation that
   keeps every promise of the parent. Otherwise hold the other object and
   delegate.
4. **Depend on small interfaces you own.** The caller defines the interface it
   needs; the callee satisfies it. Pass dependencies in (constructor or argument),
   do not reach out for them.
5. **One reason to change.** A module that changes for two unrelated reasons
   should be two modules.
6. **Make illegal states unrepresentable.** Use types, enums and constructors
   that cannot hold a bad value, instead of checks scattered around.
7. **Prefer immutable data and pure functions** for logic; keep effects (I/O,
   time, randomness) at the edges so the core is easy to test.

## Problem to pattern

| Problem | Pattern | Do not use it when |
|---|---|---|
| Behaviour varies by case and grows | Strategy (pass a function or object) | There are two cases that never change |
| Many `if type ==` branches on one value | Polymorphism or a tagged union with exhaustive match | A single small branch |
| Object has many optional parts | Builder or named arguments | Three plain fields |
| Hide a third-party or legacy API | Adapter at the boundary | You control both sides |
| Add behaviour without changing the class | Decorator or middleware | One caller needs it once |
| React to events without coupling | Observer or an event channel | Order and failure handling matter and are unclear |
| Create objects by a runtime choice | Factory function | A constructor is enough |
| Separate data access from logic | Repository over a port | The database shape is the real domain |
| Undo, queue or log an action | Command | A direct call will do |
| Swap a whole implementation in steps | Strangler (see `refactoring`) | A small local change |

## Common misuse

- **Singleton and global state:** hidden coupling and hard tests. Pass the
  instance in.
- **Deep inheritance** to share code. Extract a function or a component.
- **Interface per class** with one implementation and no second in sight.
- **Factory of factories, manager and helper classes:** names that say nothing
  about the job usually hide a missing concept.
- **Patterns as decoration:** more layers than behaviour.

## Record the choice

When a pattern shapes a public module, add one line in the design note: the
problem, the pattern, and what would make you remove it. Large choices become a
decision record (see `architecture-decisions`).

## Current tools

Idioms differ by language; follow the language skill (`lang-*`) for how a pattern
is spelled there. Many patterns are one function or one type in a modern language.
