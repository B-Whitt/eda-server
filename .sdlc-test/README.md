# SDLC-as-Skills Test Harness

End-to-end test of the harness SDLC workflow using mock data against the real eda-server codebase.

## What's Here

```
.sdlc-test/
├── README.md              ← You are here
├── jira/                  ← Mock Jira issues (markdown instead of live Jira)
│   ├── AAP-47558-epic.md  ← Epic: Management Jobs for EDA
│   ├── AAP-50001-story.md ← Story 1: Data models + migrations
│   ├── AAP-50002-story.md ← Story 2: REST API endpoints
│   ├── AAP-50003-story.md ← Story 3: Audit log cleanup job
│   └── phase-2/
│       └── TODO.md        ← Deferred work (scheduler, RBAC, more job types)
├── handbook/              ← Mock handbook docs (local instead of handbook repo)
│   ├── sdp/
│   │   └── eda-management-jobs.md        ← System Design Plan
│   └── proposals/
│       └── eda-management-jobs/
│           └── management-job-framework.md ← Technical Proposal
└── arc/
    └── config.arc.md      ← Mock ARC config (coding standards, test guidance)
```

## What's Mocked

| Real system | Mock replacement | Why |
|-------------|-----------------|-----|
| Jira Cloud | `.sdlc-test/jira/*.md` files | No live Jira writes during testing |
| Handbook repo | `.sdlc-test/handbook/` | No separate repo needed |
| ARC config hierarchy | `.sdlc-test/arc/config.arc.md` | Simplified config |
| Approvals | Auto-approved | No waiting for human review gates |
| Session recorder | Disabled | Not testing audit trail |
| Confluence | Skipped | Not needed for this test |
| Component testing | Skipped | No aap-dev needed for phase 1 |

## What's Real

| Component | Details |
|-----------|---------|
| **Codebase** | Real eda-server repo at `/Users/bwhittin/code/claude-bw-atf/eda-server` |
| **Branch** | `ai-sdlc-mngt-jobs` |
| **Git operations** | Real commits and branches |
| **Code** | Real Django models, views, serializers, tests |
| **Test execution** | Real pytest against real codebase |

## How to Run Each Phase

### Phase 1: Epic Breakdown (already done)

The epic has been broken into 3 stories with acceptance criteria.
Review the stories in `.sdlc-test/jira/` to understand the work.

**Stories (in dependency order):**
1. **AAP-50001** — Data models + migrations (no dependencies)
2. **AAP-50002** — API endpoints (depends on AAP-50001)
3. **AAP-50003** — Audit log cleanup job (depends on AAP-50001, AAP-50002)

### Phase 2: Story Implementation

Pick a story and tell the agent to implement it. The agent should:

1. Read the story from `.sdlc-test/jira/AAP-5000X-story.md`
2. Read the SDP and tech proposal from `.sdlc-test/handbook/`
3. Read existing eda-server code patterns
4. Implement the code following the patterns
5. Write tests
6. Assess adherence against acceptance criteria
7. Iterate until all criteria pass

**Example prompt:**
```
Implement the story in .sdlc-test/jira/AAP-50001-story.md

Context:
- Read the SDP at .sdlc-test/handbook/sdp/eda-management-jobs.md
- Read the tech proposal at .sdlc-test/handbook/proposals/eda-management-jobs/management-job-framework.md
- Follow existing patterns in src/aap_eda/core/models/ for model conventions
- Follow coding standards in .sdlc-test/arc/config.arc.md
- Commit with: feat(management-jobs): <description> Refs: AAP-50001
```

**Repeat for each story in order** (AAP-50001 → AAP-50002 → AAP-50003).

### Phase 3: Code Review

After implementation, review the changes:

```
Review the code changes on branch ai-sdlc-mngt-jobs.
Use the code-review approach: Functionality, Security, Quality lenses.
Reference the SDP at .sdlc-test/handbook/sdp/eda-management-jobs.md for design intent.
```

### Phase 4: Adherence Assessment

After review, check overall adherence against the epic:

```
Read the epic at .sdlc-test/jira/AAP-47558-epic.md.
For each acceptance criterion, evaluate PASS/FAIL with evidence from the implementation.
Calculate an overall intent adherence score (0-100).
```

## Success Criteria

The test is successful when:
- [ ] All 3 stories are implemented with passing tests
- [ ] Code follows existing eda-server patterns
- [ ] Code review produces actionable findings (proves the review skill works)
- [ ] Adherence assessment shows >= 80% against epic acceptance criteria
- [ ] The full flow completed without needing live Jira, handbook repo, or approvals
