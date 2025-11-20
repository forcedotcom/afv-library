---
name: WCAG Accessibility Standards (Vibes Rules)
description: Provide clear, enforceable accessibility rules for component generation based on WCAG 2.0 + 2.1 AA.
tags: wcag, accessibility, a11y, rules, components
---

# Accessibility Objectives
Agentforce Vibes must ensure every generated component is:
- **Perceivable:** Users can see or hear the content.
- **Operable:** Users can interact with all elements using a keyboard.
- **Understandable:** Content behaves predictably and clearly.
- **Robust:** Content works reliably with assistive technologies.

All rules below are mandatory unless stated otherwise.

---

# 1. PERCEIVABLE RULES

## 1.1 Text Alternatives
**Rules**
- Provide `alt` text for all meaningful images and icons.
- Use empty alt (`alt=""`) only for decorative images.

**Anti-Patterns**
- Missing `alt`.
- Using visual descriptions instead of purpose (e.g., “image of…”).

---

## 1.2 Time-Based Media
**Rules**
- Prerecorded videos must include captions.
- Provide a text alternative for audio-only or video-only content.

**Anti-Patterns**
- Videos without captions.
- Audio without transcript.

---

## 1.3 Adaptable Structure
**Rules**
- Use semantic HTML structure: headings, lists, labels.
- Maintain logical DOM order for both reading and tab flow.
- Instructions must not rely on colour, shape, or position.

**Anti-Patterns**
- `<div>` used instead of semantic tags.
- “Click the red button.”

---

## 1.4 Distinguishable Content
**Rules**
- Text contrast must be **4.5:1** or higher.
- UI element contrast must be **3:1** or higher.
- Support 200% text zoom without breaking layout.
- Do not embed text inside images.
- Layout must reflow on small screens without horizontal scrolling.

**Anti-Patterns**
- Low-contrast text.
- Tooltips that disappear too quickly.
- Layout requiring horizontal scroll on mobile.

---

# 2. OPERABLE RULES

## 2.1 Keyboard Accessibility
**Rules**
- All interactions must be keyboard-accessible.
- Tab order must be logical and sequential.
- Components must not trap keyboard focus.
- Focus must return to the triggering element when closing overlays/modals.
- Single key shortcuts must be avoidable or disabled.

**Anti-Patterns**
- Mouse-only actions.
- Unreachable or stuck focus.
- Hotkeys that trigger actions without user control.

---

## 2.2 Timing and Motion
**Rules**
- Any timed content must allow extending or disabling time limits.
- Moving/animated content must have pause or stop controls.

**Anti-Patterns**
- Auto-scrolling/rotating components without controls.

---

## 2.3 Seizure Safety
**Rules**
- Do not include flashing content.

**Anti-Patterns**
- Any animation flashing more than 3 times in one second.

---

## 2.4 Navigable Content
**Rules**
- Provide a "Skip to main content" link as the first focusable element.
- Use clear, descriptive page titles.
- Use descriptive headings/labels.
- All focus states must be clearly visible and high contrast.
- Links must clearly indicate purpose.

**Anti-Patterns**
- “Click here.”
- Hidden or low-contrast focus outlines.
- Sticky headers covering focused elements.

---

# 3. UNDERSTANDABLE RULES

## 3.1 Readable Content
**Rules**
- The page must declare a correct `lang` attribute.
- Mark text written in other languages with proper `lang=""`.

**Anti-Patterns**
- Missing or incorrect language attributes.

---

## 3.2 Predictable Behaviour
**Rules**
- Do not trigger actions automatically on focus or input.
- Navigation patterns must remain consistent across components.
- UI elements with the same purpose must use consistent labels and icons.

**Anti-Patterns**
- Auto-submit fields.
- Dropdown selection triggering automatic navigation.

---

## 3.3 Input Assistance
**Rules**
- Every input must have an explicit visible label.
- Error messages must clearly identify the issue.
- Error messages must suggest how to fix the issue.
- Use semantic autocomplete attributes for known fields (e.g., name, email).

**Anti-Patterns**
- Placeholder text acting as label.
- Generic errors like “Invalid field.”

---

# 4. ROBUST RULES

## 4.1 Compatible Code
**Rules**
- Components must expose correct name, role, and value for assistive tech.
- Prefer native HTML elements for buttons, inputs, links, etc.
- Use ARIA roles and attributes only when no native element exists.
- Notify assistive technologies of dynamic updates using `aria-live` where appropriate.

**Anti-Patterns**
- Custom elements replacing native functionality without equivalent semantics.
- Overusing ARIA roles in place of native HTML.

---

# SUMMARY OF REQUIREMENTS (FOR VIBES)
- Use semantic structure.
- Maintain high contrast.
- Ensure predictable behaviour.
- Support full keyboard operation.
- Provide clear labels, errors, and instructions.
- Avoid colour-only meaning.
- Avoid hidden or weak focus states.
- Do not embed text in images.
- Do not use visual-only cues.
- Use ARIA only when absolutely required.

