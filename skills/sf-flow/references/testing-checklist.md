<!-- Parent: sf-flow/SKILL.md -->
# Flow Testing Checklist

> **Version**: 2.0.0
> **Purpose**: Quick-reference checklist for flow testing
> **Usage**: Copy and use for each flow deployment

---

## Pre-Testing Setup

- [ ] Flow XML validates without errors
- [ ] All decision paths documented
- [ ] Test data prepared in sandbox
- [ ] Debug logs enabled for test user

---

## Path Coverage

- [ ] All decision branches tested (including default)
- [ ] All loop scenarios tested:
  - [ ] 0 items (empty collection)
  - [ ] 1 item
  - [ ] Many items (10+)
- [ ] All fault paths tested
- [ ] Positive cases pass (valid inputs)
- [ ] Negative cases handled gracefully (invalid inputs)

---

## Bulk Testing

- [ ] Single record works correctly
- [ ] 10-20 records work (basic bulkification)
- [ ] 200+ records work (no governor limit errors)
- [ ] No DML-in-loop errors in debug logs

---

## Edge Cases

- [ ] Null values handled (no crashes)
- [ ] Empty collections handled (loops skip gracefully)
- [ ] Max field lengths work (no truncation)
- [ ] Special characters work (`<>&"'`)
- [ ] Date edge cases work (leap years, boundaries)

---

## User Context

- [ ] Works as System Administrator
- [ ] Works as Standard User
- [ ] FLS restrictions enforced (User mode flows)
- [ ] Sharing rules respected
- [ ] Custom permissions work (`$Permission`)

---

## Error Handling

- [ ] All DML elements have fault paths
- [ ] Error messages are user-friendly
- [ ] Rollback logic works (if multi-step DML)
- [ ] Error logging captures context

---

## Screen Flow Specific

- [ ] All navigation works (Next/Previous/Finish)
- [ ] Input validation works on each screen
- [ ] Conditional visibility works
- [ ] Progress indicator updates (if applicable)
- [ ] Back button behavior correct

---

## Record-Triggered Specific

- [ ] Entry conditions filter correctly
- [ ] Before-save vs After-save timing correct
- [ ] `$Record` values accessible
- [ ] Re-entry prevention works (if applicable)

---

## Scheduled Flow Specific

- [ ] Schedule configuration verified
- [ ] Manual run test passes
- [ ] Empty result set handled
- [ ] Batch processing works

---

## Deployment

- [ ] `checkOnly=true` deployment succeeds
- [ ] package.xml API version matches flow
- [ ] Test in sandbox complete
- [ ] Activation plan documented

---

## Post-Deployment

- [ ] Flow status verified (Active/Draft)
- [ ] Correct version is active
- [ ] No errors in Flow Errors log
- [ ] First execution monitored

---

## Sign-Off

| Item | Completed | Date | Tester |
|------|-----------|------|--------|
| Development Testing | | | |
| UAT Testing | | | |
| Bulk Testing | | | |
| Security Review | | | |
| Production Deployment | | | |

---

## Notes

_Add any flow-specific notes or exceptions here_
