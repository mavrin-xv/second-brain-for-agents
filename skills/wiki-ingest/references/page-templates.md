# Wiki page templates

Keep pages short and dense. A page that needs scrolling should probably be two pages.

## Source page: `wiki/sources/<slug>.md`

```markdown
---
type: source
title: Pottery newsletter teardown
created: 2026-02-11
raw: raw/2026-02-10-email-teardown-of-a-pottery-newsletter.md
reviewed: false
confidence: medium
tags: [email, drops]
---
# Pottery newsletter teardown

**What:** teardown of a studio newsletter, article, author unknown, Feb 2026.

## Claims worth keeping
- One email per kiln firing, not per week. Each shows three finished pieces, the firing date and a fixed drop time.
- Pieces sell out within an hour; the stated reason is that the drop is small and dated.
- Weekly digests were tried and dropped; the source gives no numbers.

## Not covered
List size, prices, how the studio grew the list.

Feeds: [[concepts/kiln-drop-emails]], [[concepts/drop-scarcity]]
```

## Concept page: `wiki/concepts/<slug>.md`

```markdown
---
type: concept
title: Kiln drop emails
created: 2026-02-11
updated: 2026-03-02
sources: [sources/pottery-newsletter-teardown, sources/drop-timing-thread]
reviewed: false
confidence: high
tags: [email]
---
# Kiln drop emails

**In one line:** one email per firing with a fixed drop time beats a weekly digest for a small studio.

## How it works
- Three finished pieces per email, firing date, fixed drop time ([[sources/pottery-newsletter-teardown]]).
- Announce the drop time two days ahead ([[sources/drop-timing-thread]]).

## When it does not apply
Large catalogs with steady stock. Inference: scarcity needs a small, dated batch ([[sources/pottery-newsletter-teardown]]).

## Open questions
- Source A says subject lines should name the glaze; source B says name the piece. Untested here.

Related: [[concepts/drop-scarcity]], [[entities/kiln-supply-co]]
```

## Entity page: `wiki/entities/<slug>.md`

```markdown
---
type: entity
title: Kiln Supply Co
created: 2026-02-12
sources: [sources/supplier-call-notes]
reviewed: false
url: https://example.com
---
# Kiln Supply Co

**What:** supplier of kiln shelves and cones.

## Facts
- Winter lead time 3 weeks ([[sources/supplier-call-notes]]).

## Our history with them
- 2026-02: ordered cone 6 shelves. See [[decisions/2026-02-15-second-supplier]].
```

## Answer page: `wiki/answers/<slug>.md`

```markdown
---
type: answer
title: Should we raise mug prices before the spring drop?
created: 2026-03-04
question: Should we raise mug prices before the spring drop?
sources: [sources/pricing-handmade-goods-thread]
reviewed: false
---
# Should we raise mug prices before the spring drop?

**Short answer:** yes, to the hourly-rate floor, because ...

## Reasoning
...

## What would change this answer
...
```
