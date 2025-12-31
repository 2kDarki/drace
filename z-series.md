# Z-Series Rules

The Z-Series rules are a small set of practical guidelines for writing better software.

They are inspired by ideas from *The Pragmatic Programmer*, but simplified and adapted for everyday development.  
The focus is on writing code that is easy to understand, change, and maintain.

These rules are not strict laws. They are reminders to help developers make better decisions.

---

## Z1. Own the Code You Change

If you modify a piece of code, you are responsible for it.

Do not leave broken tests, unclear logic, or unfinished changes behind.  
Every change should leave the codebase in a stable and readable state.

---

## Z2. Make Changes Easy

Software will change. Always.

Write code in a way that small changes are safe and simple.  
Avoid tight coupling and hard-coded assumptions that make changes risky.

---

## Z3. Avoid Duplicating Knowledge

Do not repeat the same logic or rules in multiple places.

When the same knowledge exists in more than one place, it becomes hard to maintain and easy to break.  
Keep important logic in one clear location.

---

## Z4. Write Code for People

Code is read more often than it is written.

Use clear names, simple structures, and readable logic.  
If someone else cannot understand your code quickly, it needs improvement.

---

## Z5. Fail Early and Clearly

Errors should be detected as soon as possible.

Validate inputs, check assumptions, and surface problems immediately.  
Silent failures are difficult to debug and expensive to fix.

---

## Z6. Prefer Clear Code Over Clever Code

Clever solutions often cause confusion later.

Simple and obvious code is easier to maintain than complex abstractions.  
If clarity and cleverness conflict, choose clarity.

---

## Z7. Automate Repetitive Tasks

If a task is repeated often, automate it.

This includes testing, formatting, building, and validation.  
Automation reduces human error and saves time.

---

## Z8. Keep Learning

Tools and best practices change over time.

Developers should continuously learn and improve their skills.  
A healthy codebase evolves instead of staying static.

---

## Z9. Solve the Problem You Have

Do not overengineer for imaginary future requirements.

Build what is needed now, but keep the design flexible enough to change later.  
Complexity should be added only when it is required.

---

## Z10. Take Responsibility

Take ownership of mistakes and fix them.

Blaming tools, teammates, or circumstances does not improve software.  
Professional development requires accountability.
