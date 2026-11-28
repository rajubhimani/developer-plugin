---
name: accessibility
description: "Accessible UI: semantic HTML, keyboard, focus, contrast, labels, WCAG. Use when building or fixing a page or form, or screen reader users report problems."
metadata:
  verified: "2026-11-19"
---

# Accessibility

Accessible by default costs little at the start and a lot to retrofit. Target the
current Web Content Accessibility Guidelines (WCAG) at level AA unless the project
says otherwise; look up the exact current criteria.

## Build rules

1. **Use native elements.** A button, link, input, heading, list, table, nav or
   main region carries meaning and keyboard behaviour for free. Use a generic
   container with extra attributes only when no native element fits; ARIA that
   contradicts the element is worse than none.
2. **Headings and landmarks form an outline** a screen reader user can jump
   through: one main heading, no skipped levels, regions labelled when repeated.
3. **Everything works by keyboard,** in a logical order, with no keyboard trap.
   Add a skip link. Custom widgets follow the standard keyboard pattern for their
   role.
4. **Focus is always visible** and never hidden by sticky content. Move focus
   deliberately on route changes, dialogs and errors, and return it on close.
5. **Text alternatives:** meaningful images get a description of their purpose;
   decorative ones get an empty alternative; icon-only controls get an accessible
   name.
6. **Colour contrast** meets the WCAG ratios for text and for interface parts and
   focus indicators. Never use colour alone to carry meaning (add text or an icon).
7. **Forms:** every input has a visible, associated label; errors are specific,
   tied to the field, announced, and say how to fix; do not clear entered data.
   Use the right input type and autocomplete hint.
8. **Size and reflow:** content works at large text sizes and zoom without loss
   or two-way scrolling; touch targets are big enough and spaced.
9. **Motion and time:** respect the user's reduced-motion setting, give a way to
   pause anything that moves, and do not flash. Do not put hard time limits
   without a way to extend.
10. **Dynamic content:** announce status changes (live regions) without moving
    focus; loading states are communicated, not just shown.
11. **Media:** captions for video, transcripts for audio.
12. **Language and titles:** set the page language and a unique page title.

## Test

1. **Automated checks** in CI and in component tests, with the project's
   accessibility test tool. They catch only a part of the problems.
2. **Keyboard-only pass** of each new flow.
3. **Screen reader spot check** on the main flow with a common reader for the
   platform.
4. **Zoom, large text and high-contrast** check.
5. Add an accessibility line to the review: new controls, focus, labels, contrast.

## Related

`lang-typescript-react`, `testing-strategy`, `code-review-checklist`.
