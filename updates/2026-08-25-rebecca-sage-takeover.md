# Message to Rebecca — Sage (2026-08-25)

> **Two versions below.** Use **A** if we ran `grant_sage_gateway.py --grant` and Sage is
> already flowing — it asks her for nothing. Use **B** only if that route was rejected and she
> genuinely has to click Take over herself.
>
> Prefer A. She has enough on. The ownership question is ours to solve, not hers to absorb.

---

## VERSION A — nothing needed from her (preferred)

Hi Rebecca,

Sage is flowing into Fabric as of today, and I wanted to flag one correction plus two
questions. Nothing here needs you to do anything.

**The correction:** I'd been telling you Sage was blocked waiting on a gateway permission from
your side. It wasn't. I looked properly today and you and IT have had "Can use" on the Sage
connection the whole time — it was there before I ever asked. The actual problem was mine: a
dataflow runs as whoever *owns* it, and I'd built ours under my account, which had no gateway
rights. So it failed and I reported it as your blocker. Sorry for the runaround — that one's
on me, and it cost about three weeks of it sitting on your list.

It's sorted now and pulling all 8 Sage tables, including the two **line-item** tables
(`arivln` / `apivln`) that the existing dataflow explicitly drops. That's where retainage and
cost-code-level AP detail live — nobody's had visibility into that until now.

### Two things worth a minute, whenever

1. **The gateway has no human administrator.** It's registered under
   `fabricconnector@affect-group.com`, and as far as I can tell nobody — not you, not Cal —
   holds gateway admin rights. Nerds That Care handed Affect responsibility for gateway
   administration (it's in their handoff doc) without anyone getting the ability to do it.
   Worth asking them to **add you as gateway admin** — one click for them, and it removes a
   real single point of failure. The 1Password links holding the recovery key expired in May,
   so right now if that gateway needed attention, nobody could give it.

2. **There's a third Sage database I didn't know about.** The gateway exposes `ABMI`,
   `Affect Group`, and **`Make By Affect`**. We're on `Affect Group` and I'm confident that's
   right — it resolves to 15 of the 16 live Procore projects and $22.5M of AR. But is
   **Make By Affect** a separate book that should be in the reporting too? Don't want to
   quietly leave a whole entity out.

Separately: Procore extraction now runs inside Fabric on the nightly schedule instead of on my
laptop, and five feeds that had never returned a single row — contract line items, payment
applications, budget detail — are landing for the first time. Happy to walk you through what
was wrong there whenever you want a session; it's a good one for the recorded series.

Thanks,
Charley

---

## VERSION B — she takes ownership herself (only if A was refused)

---

Hi Rebecca,

Two things — one is good news and one is me correcting myself.

**The correction first.** I've been telling you Sage was blocked on a gateway permission
grant. It wasn't. I signed into the gateway today and you and IT have *already* had "Can use"
on the Sage connection this whole time — it was there before I ever asked. The real problem
was on my side: a Dataflow Gen2 runs as whoever **owns** it, and I'd built `CD_Sage_Ingest`
under my account, which has no gateway rights. So it failed, and I reported it as something
you needed to grant me. Sorry for the runaround — that one's mine.

**The good news:** it means you can turn Sage on yourself right now, and it costs nothing.

## What to do — about 2 minutes

**Take ownership of the dataflow**

https://app.fabric.microsoft.com/groups/1f7caed6-f88a-4e52-bc83-9a498a165301/dataflows-gen2/9d1dc6db-405b-4cc6-bd3e-a8fdb8795ab8?experience=fabric-developer

1. Go to the **Build** workspace, open the **`charley-dev`** folder, and find
   **`CD_Sage_Ingest`**.
   *Only the dataflow matters — folders in Fabric are just labels, there's no ownership on
   them, so there's nothing to do at the `charley-dev` level.*
2. Hover the row → click the **`...`** (More options) → **Take over**
   *(may read "Take ownership" — same thing).*
3. Open the dataflow. If it prompts you to **set/edit credentials** for the SQL connection,
   accept — it's already pointed at the gateway and the **`Affect Group`** database, which is
   the one you have rights on. Connection type **SQL Server**, auth **Basic**.
4. **Save / Publish**, then **Refresh now** from the `...` menu.

No new licence, no admin rights, nothing from Nerds That Care.

### If "Take over" isn't in that menu

Two other places it lives, depending on how your view is set:

- Open the dataflow → **Settings** (gear) → **Owner** → *Take over*
- Or in the dataflow editor: **Home → Manage connections** → the Sage connection → **Edit**,
  and sign in there

If none of those show it, stop and tell me — there's a service-account route that needs
nothing from you, and it's not worth you hunting through menus.

## How we'll know it worked

- **Refresh history** on the dataflow shows **Succeeded**. First run takes a few minutes —
  it's pulling 8 tables.
- **8 new tables** appear in `CD_Bronze_Lakehouse`:
  `cd_bronze_sage_acrinv`, `arivln`, `acrpmt`, `acpinv`, `apivln`, `acppmt`, `actrec`, `actpay`.

If the refresh **fails**, the message matters — send me a screenshot rather than retrying.
"Credentials" means step 3 needs redoing; anything mentioning the gateway means I've got
something else wrong and I'll fix it from my side.

Ping me once it's green and I'll check the row counts and start building silver on top. The
two **line-item** tables (`arivln`, `apivln`) are what I'm most interested in — they're where
retainage and cost-code-level AP actually live, and the current dataflow explicitly strips out
the columns that point at them, so nobody has ever looked at that detail.

## Two other things, whenever you have a minute

1. **The gateway has no human administrator.** It's registered under
   `fabricconnector@affect-group.com`, and as far as I can tell nobody — not you, not Cal — has
   gateway admin rights. Nerds That Care handed Affect responsibility for gateway
   administration but not the ability to do it. Worth asking them to **add you as a gateway
   admin**; it's one click for them and it removes a real single point of failure. (The
   1Password links with the recovery key expired back in May, so right now if that gateway
   needed attention, nobody could give it.)

2. **There's a third Sage database I didn't know about.** The gateway exposes `ABMI`,
   `Affect Group`, and **`Make By Affect`**. We're using `Affect Group` and I'm confident
   that's right — it resolves to 15 of the 16 live Procore projects and $22.5M of AR. But is
   **Make By Affect** a separate book that should also be in the reporting? Don't want to
   quietly leave a whole entity out.

Separately — Procore extraction now runs inside Fabric on the nightly schedule rather than on
my laptop, and five feeds that had never returned a single row (contract line items, payment
applications, budget detail) are now landing. Happy to walk you through what was wrong there
whenever you want a session.

Thanks,
Charley

---

## Notes for us, not for Rebecca

- Owner takeover for **Dataflow Gen2** is a portal action. The Power BI `Default.Takeover`
  API does not cover Gen2 — `GET /groups/{id}/dataflows` returns an empty list for this
  workspace while `CD_Sage_Ingest` plainly exists, so Gen2 items are not on that surface.
  `grant_sage_gateway.py --take-ownership` is annotated accordingly; a 404 there means "use
  the portal", not a broken account.
- The fallback referred to obliquely at the end of the "if Take over isn't there" section is
  `grant_sage_gateway.py --grant`, which the gateway's registration account can run. Kept
  vague on purpose: it works, but it ties Sage to a consultant's account and should not be
  the thing she reaches for first.
- Durable end state is still `fabricconnector@` owning the dataflow, which needs it added to
  the workspace plus a Pro licence ($14/mo). Not raised in this message — one ask at a time,
  and the free one lands first.
